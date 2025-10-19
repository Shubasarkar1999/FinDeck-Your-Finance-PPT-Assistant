import os
import json
import re
import vertexai
from vertexai.generative_models import GenerativeModel
from fastapi import FastAPI, HTTPException
# Make sure your models.py includes 'language' in the AnalysisResultPayload
from models import AnalysisResultPayload, ContentResult

# --- FastAPI App and Vertex AI Initialization ------------------------------
app = FastAPI(
    title="Content Generation Service",
    description="Generates presentation content using Gemini.",
    version="2.1.0",
)

try:
    PROJECT_ID = os.environ.get("GCP_PROJECT")
    LOCATION = os.environ.get("GCP_REGION")
    if not PROJECT_ID or not LOCATION:
        raise ValueError("GCP_PROJECT and GCP_REGION environment variables are not set.")
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = GenerativeModel("gemini-2.5-flash")
    print("✅ Vertex AI initialized successfully in Content Generation Service.")
except Exception as e:
    print(f"❌ ERROR: Failed to initialize Vertex AI: {e}")
    model = None

# --- Helper Function (No changes here) ---------------------------------------
def extract_json_from_string(text: str) -> str:
    """
    Safely extracts a JSON object from a string, even with markdown fences.
    """
    pattern = r'```json\s*(\{.*?\})\s*```'
    fallback_pattern = r'(\{.*?\})'
    
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    
    match = re.search(fallback_pattern, text, re.DOTALL)
    return match.group(1) if match else ""

# --- API Endpoint (Updated) ------------------------------------------------
@app.post("/generate-content", response_model=ContentResult)
async def generate_content(request: AnalysisResultPayload):
    """
    Generates the full presentation content (titles and bullet points)
    in a single, efficient API call, now including language.
    """
    if not model:
        raise HTTPException(status_code=503, detail="Vertex AI model not available.")

    print(f"--- Generating content for topic: '{request.topic[:80]}...' in {request.language} ---")

    # --- START OF CHANGE ---
    # The prompt is updated to include the language parameter.
   # This is the new prompt for your content-generation-service
    prompt = f"""
    You are an expert in creating professional presentations for the financial sector.
    Your task is to generate the content for a presentation. For each slide, you must choose the best layout to represent the information.

    The user's request is: "{request.topic}"
    The target audience is: "{request.target_audience}"
    The desired number of slides is: {request.slide_count}
    The presentation language MUST be: "{request.language}"

    AVAILABLE LAYOUTS:
    - "title_slide": For the main title. Use for the first slide. Data required: {{ "title": "...", "subtitle": "..." }}
    - "bullet_points": A standard slide with a title and several bullet points. Data required: {{ "title": "...", "points": ["...", "..."] }}

    CRITICAL INSTRUCTIONS:
    1. Your entire response MUST be a single, clean JSON object.
    2. The root of the JSON object must be a "slides" array.
    3. Each object in the "slides" array must have two keys: "layout" (the name of the chosen layout) and "data" (a JSON object containing the required information for that layout).
    4. Each slide should have 4-5 bullet points and the word count should not exceed 25 words for each bullet point.
    Example of a perfect response:
    {{
    "slides": [
        {{
        "layout": "title_slide",
        "data": {{ "title": "The Future of DeFi", "subtitle": "An overview" }}
        }},
        {{
        "layout": "numbered_bullets",
        "data": {{ "title": "Key Challenges", "items": ["Security Risks", "Scalability Issues", "Regulatory Uncertainty"] }}
        }}
    ]
    }}

    Ensure the JSON is perfectly formatted.
    """
    # --- END OF CHANGE ---
    try:
        response = await model.generate_content_async(prompt)
        json_string = extract_json_from_string(response.text)

        if not json_string:
            raise ValueError("Failed to extract JSON from the AI's response.")

        content_data = json.loads(json_string)
        result = ContentResult(**content_data)
        
        print(f"--- Successfully generated content for {len(result.slides)} slides. ---")
        return result

    except Exception as e:
        print(f"--- CRITICAL ERROR in Content Generation: {e} ---")
        raw_response_text = "N/A"
        if 'response' in locals() and hasattr(response, 'text'):
            raw_response_text = response.text
        raise HTTPException(status_code=500, detail=f"Failed to generate content: {e}. Raw AI Response: {raw_response_text}")
