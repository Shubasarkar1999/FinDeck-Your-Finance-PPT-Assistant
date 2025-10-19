import os
import base64
import asyncio
import logging
from typing import List, Tuple

from fastapi import FastAPI, HTTPException
from google.api_core.exceptions import ResourceExhausted
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from vertexai.generative_models import GenerativeModel

# Import the Pydantic models
from models import ImageGenerationRequest, ImageServiceResponse, Slide

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="Image Generation Service",
    description="Generates images for presentation slides based on provided content."
)

# --- Initialize Vertex AI ---
try:
    PROJECT_ID = os.environ.get("GCP_PROJECT")
    LOCATION = "us-central1"
    if not PROJECT_ID:
        raise ValueError("GCP_PROJECT environment variable is not set.")

    vertexai.init(project=PROJECT_ID, location=LOCATION)
    
    image_model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-002")
    text_model = GenerativeModel("gemini-2.5-flash")
    
    logging.info("✅ Vertex AI models initialized successfully.")
except Exception as e:
    logging.critical(f"Failed to initialize Vertex AI models: {e}", exc_info=True)
    image_model = None
    text_model = None

# --- REMOVED: assess_image_necessity function is no longer needed ---

def extract_content_from_slide(slide: Slide) -> Tuple[str, List[str]]:
    """Intelligently extracts the title and content from a slide."""
    data = slide.data
    title = data.title or "Untitled"
    content_list = data.points or data.items or []
    
    if data.subtitle:
        content_list.insert(0, data.subtitle)
    if data.message:
        content_list.append(data.message)
        
    return title, [item for item in content_list if item]

async def generate_image_prompt(slide_title: str, slide_content: List[str], theme: str) -> str:
    """Uses Gemini to generate a concise and effective image prompt."""
    if not text_model:
        return f"A professional, {theme}-themed image about {slide_title}"
    
    content_str = "; ".join(slide_content)
    prompt_template = f"""
    Create a short, professional, and visually clear image prompt (under 15 words) for a business presentation slide.
    The image should be a simple, clean, and abstract visual metaphor for the slide's core concept.
    Avoid text, complex scenes, or people's faces. Focus on minimalist, corporate aesthetics.

    Theme: "{theme}"
    Slide Title: "{slide_title}"
    Slide Content: "{content_str}"
    
    Example Output: Minimalist glowing data charts and graphs on a clean background.
    """
    try:
        response = await text_model.generate_content_async(prompt_template)
        clean_prompt = response.text.strip().replace('"', '')
        logging.info(f"Generated prompt for '{slide_title}': '{clean_prompt}'")
        return clean_prompt
    except Exception as e:
        logging.error(f"Error generating prompt for '{slide_title}': {e}")
        return f"A high-quality, {theme}-themed abstract image about {slide_title}"

# Limit concurrent calls to the image generation API to avoid quota errors
MAX_CONCURRENT_IMAGES = 1
image_gen_semaphore = asyncio.Semaphore(MAX_CONCURRENT_IMAGES)

async def generate_single_image(prompt: str) -> str:
    """Generates a single image with concurrency limiting and retry logic."""
    if not image_model:
        raise HTTPException(status_code=503, detail="Imagen model not available.")
    
    async with image_gen_semaphore:
        for attempt in range(3):
            try:
                # Run the blocking function in a separate thread
                response = await asyncio.to_thread(
                    image_model.generate_images,
                    prompt=prompt, 
                    number_of_images=1, 
                    aspect_ratio="16:9"
                )
                return base64.b64encode(response[0]._image_bytes).decode("utf-8")
            except ResourceExhausted as e:
                logging.warning(f"Quota exceeded on attempt {attempt + 1}. Retrying... Error: {e}")
                await asyncio.sleep(20 * (attempt + 1))
            except Exception as e:
                logging.warning(f"Image generation attempt {attempt + 1} failed. Retrying... Error: {e}")
                await asyncio.sleep(2 * (attempt + 1))
        
        raise HTTPException(status_code=500, detail=f"Failed to generate image for prompt '{prompt}' after retries.")
    
@app.post("/generate-images", response_model=ImageServiceResponse)
async def generate_images(request: ImageGenerationRequest):
    """
    Receives a list of slides, generates an image for each one, and returns
    the updated list of slides with the 'image_base64' field populated.
    """
    if not image_model or not text_model:
        raise HTTPException(status_code=503, detail="AI models are not available.")
    
    # Step 1: Generate all image prompts in parallel
    prompt_generation_tasks = []
    for slide in request.slides:
        title, content = extract_content_from_slide(slide)
        prompt_generation_tasks.append(generate_image_prompt(title, content, request.theme))
    
    image_prompts = await asyncio.gather(*prompt_generation_tasks, return_exceptions=True)

    # Step 2: Generate all images in parallel
    image_generation_tasks = []
    for prompt in image_prompts:
        if isinstance(prompt, Exception):
            # If prompt generation failed, we can't generate an image
            image_generation_tasks.append(asyncio.sleep(0, result=None)) # Placeholder for failed prompt
        else:
            image_generation_tasks.append(generate_single_image(prompt))
            
    images_base64 = await asyncio.gather(*image_generation_tasks, return_exceptions=True)

    # Step 3: Populate the original slide objects with the generated images
    updated_slides = []
    for i, slide in enumerate(request.slides):
        base64_image = images_base64[i]
        if base64_image and not isinstance(base64_image, Exception):
            slide.image_base64 = base64_image
        updated_slides.append(slide)

    logging.info(f"✅ Successfully processed images for {len(updated_slides)} slides.")
    return ImageServiceResponse(slides_with_images=updated_slides)