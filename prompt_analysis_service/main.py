import os
import json
import re
from fastapi import FastAPI, HTTPException
from models import UserPromptRequest, AnalysisResult
from finance_checker import is_finance_topic

# MODIFIED: Import Vertex AI libraries
import vertexai
from vertexai.generative_models import GenerativeModel

# MODIFIED: Initialize Vertex AI
# Make sure to set your project and location in your environment
# or replace them here.
PROJECT_ID = os.environ.get("GCP_PROJECT")
LOCATION = os.environ.get("GCP_REGION")
vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel("gemini-2.5-flash")

app = FastAPI()

def extract_json_from_string(text: str) -> str:
    match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        return match.group(1)
    # Fallback for non-fenced JSON
    match = re.search(r'(\{.*?\})', text, re.DOTALL)
    if match:
        return match.group(1)
    return ""

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_prompt(request: UserPromptRequest):
    # --- ADDED LOGGING ---
    print("--- PROMPT ANALYSIS SERVICE: /analyze endpoint invoked ---")
    print(f"--- Received prompt: {request.prompt[:100]}... ---")

    if not await is_finance_topic(request.prompt):
        print("--- PROMPT ANALYSIS SERVICE: Topic is not finance. Raising 400 error. ---")
        raise HTTPException(status_code=400, detail="I am specialized in generating presentations for the financial sector only.")

    extraction_prompt = f"""
    Analyze the user's request and extract the following information into a single, clean JSON object.
    - topic: The main subject of the presentation.
    - theme: The user's desired visual style. If not mentioned, default to "professional and clean".
    - slide_count: The number of slides requested as an integer. If not specified, default to 7.
    - target_audience: The intended audience. If not mentioned, default to "Knowledgeable Audience".

    Your entire response MUST be only the JSON object, enclosed in ```json ... ```.

    User Request: "{request.prompt}"
    """

    try:
        # --- ADDED LOGGING ---
        print("--- PROMPT ANALYSIS SERVICE: Sending request to Vertex AI... ---")
        response = model.generate_content(extraction_prompt)
        
        # --- ADDED LOGGING ---
        print(f"--- PROMPT ANALYSIS SERVICE: Raw response from Vertex AI: ---\n{response.text}\n--------------------")
        
        json_string = extract_json_from_string(response.text)

        if not json_string:
             print("--- PROMPT ANALYSIS SERVICE: ERROR - Failed to extract JSON from AI response. ---")
             raise ValueError("Failed to extract JSON from the model's response.")

        extracted_data = json.loads(json_string)
        print("--- PROMPT ANALYSIS SERVICE: Successfully parsed JSON. Returning data. ---")
        return AnalysisResult(**extracted_data)

    except Exception as e:
        print(f"--- PROMPT ANALYSIS SERVICE: CRITICAL ERROR in try block: {e} ---")
        # This will now include the raw response in the error detail for better debugging
        raw_response_text = "N/A"
        if 'response' in locals() and hasattr(response, 'text'):
            raw_response_text = response.text
        
        raise HTTPException(status_code=500, detail=f"Failed to extract details from prompt: {e}. Raw AI Response: {raw_response_text}")
