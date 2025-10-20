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

    # --- START OF CORRECTION ---
    # The prompt is relaxed. It now asks for a MIX of general points and
    # data-supported points, making citations optional and more natural.
    prompt = f"""
    You are an expert in creating professional presentations for the financial sector.
    Your task is to generate compelling content. Create a good mix of high-level, insightful points and points supported by specific data.

    # --- CONTENT GUIDELINES ---
    - **Factual & Current:** Where appropriate, support key arguments with verifiable facts, statistical figures, or recent news (from the last 12-18 months).
    - **Natural Sourcing:** When you state a specific statistic or a critical data point, it is good practice to cite the source briefly in parentheses at the end of that bullet point. For example: (Source: Bloomberg, Oct 2025).
    - **Balance is Key:** Do NOT add a citation to every bullet point. The majority of points should be general analysis and insights. Only use citations for specific, hard numbers or facts to add credibility where it counts the most.

    # --- USER REQUEST ---
    - The user's request is: "{request.topic}"
    - The target audience is: "{request.target_audience}"
    - The desired number of slides is: {request.slide_count}
    - The presentation language MUST be: "{request.language}"

    # --- AVAILABLE LAYOUTS & JSON STRUCTURE ---
    - "title_slide": For the main title. Use for the first slide. Data required: {{ "title": "...", "subtitle": "..." }}
    - "bullet_points": A standard slide with a title and several bullet points. Data required: {{ "title": "...", "points": ["...", "..."] }}

    # --- CRITICAL INSTRUCTIONS ---
    1.  Your entire response MUST be a single, clean JSON object.
    2.  The root of the JSON object must be a "slides" array.
    3.  Each object must have "layout" and "data" keys.
    4.  Each slide should have 4-5 concise bullet points (under 25 words each).

    # --- EXAMPLE OF A PERFECT RESPONSE (Shows a natural mix of points) ---
    {{
    "slides": [
        {{
            "layout": "title_slide",
            "data": {{ "title": "The Future of DeFi", "subtitle": "An Overview" }}
        }},
        {{
            "layout": "bullet_points",
            "data": {{
                "title": "Key Market Trends",
                "points": [
                    "Increasing institutional adoption is driving market maturity and stability.",
                    "The global DeFi market is projected to exceed $200 billion by 2028 (Source: Grand View Research).",
                    "A major focus is now shifting towards improving user experience and accessibility for broader adoption.",
                    "Regulatory frameworks are slowly beginning to take shape across major global economies."
                ]
            }}
        }}
    ]
    }}

    Ensure the JSON is perfectly formatted.
    """
    # --- END OF CORRECTION ---
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