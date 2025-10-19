import os
import json
import re
import vertexai
from vertexai.generative_models import GenerativeModel
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# --- Pydantic Models --------------------------------------------------------

class UserPromptRequest(BaseModel):
    """Defines the expected input format for the /analyze endpoint."""
    prompt: str

class AnalysisResult(BaseModel):
    """Defines the successful output format for the /analyze endpoint."""
    topic: str
    theme: str
    slide_count: int
    target_audience: str

# --- FastAPI App and Vertex AI Initialization ------------------------------

app = FastAPI(
    title="Prompt Analysis Service",
    description="Classifies prompts and extracts presentation requirements using Gemini.",
    version="1.0.0",
)

try:
    PROJECT_ID = os.environ.get("GCP_PROJECT")
    LOCATION = os.environ.get("GCP_REGION")
    if not PROJECT_ID or not LOCATION:
        raise ValueError("GCP_PROJECT and GCP_REGION environment variables are not set.")
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    
    # --- THIS IS THE FIX ---
    # The previous code used 'gemini-1.5-flash-latest', which is being retired.
    # We are upgrading to the latest stable model based on the lifecycle documentation.
    model = GenerativeModel("gemini-2.5-flash")
    
    print("✅ Vertex AI initialized successfully in Prompt Analysis Service.")
except Exception as e:
    print(f"❌ ERROR: Failed to initialize Vertex AI in Prompt Analysis Service: {e}")
    model = None

# --- Core Logic Functions ----------------------------------------------------

async def is_finance_topic(user_prompt: str) -> bool:
    """Uses a combination of keyword checks and AI to classify if a prompt is finance-related."""
    if not model:
        raise HTTPException(status_code=503, detail="Vertex AI model not available.")

    # Simple keyword check for obvious cases to improve speed and accuracy
    simple_prompt = user_prompt.lower().strip()
    if simple_prompt == "finance":
        print("Finance check for 'finance': Yes (Keyword Match)")
        return True

    system_prompt = """
    You are a highly accurate classification agent. Your task is to determine if a user's request is related to the financial sector.
    A request is financial if its core subject involves money, capital, assets, liabilities, markets, investments, risk, or the economic performance of an entity.
    To answer, you MUST provide a one-sentence Rationale, then on a new line, provide the final Response: "Yes" or "No".

    ---
    Example 1:
    User Request: "Tell me about the current price of Bitcoin."
    Rationale: The request is about the price of a digital asset, which falls under investments and financial markets.
    Response: Yes
    ---
    Example 2:
    User Request: "What's the best recipe for chocolate cake?"
    Rationale: The request is about cooking, which has no direct connection to financial markets.
    Response: No
    ---
    Example 3:
    User Request: "The impact of AI on investment banking."
    Rationale: The request is about investment banking, which is a core component of the financial sector.
    Response: Yes
    ---
    """
    full_prompt = f'{system_prompt}\nUser Request: "{user_prompt}"'

    try:
        response = await model.generate_content_async(full_prompt)
        last_line = response.text.strip().lower().splitlines()[-1]
        final_answer = last_line.replace("response:", "").strip()
        print(f"Finance check for '{user_prompt[:40]}...': {final_answer}")
        return "yes" in final_answer
    except Exception as e:
        print(f"❌ ERROR during finance classification: {e}")
        return False # Default to False on API error

def extract_json_from_string(text: str) -> str:
    """Safely extracts a JSON object from a string, even with markdown fences."""
    match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r'(\{.*?\})', text, re.DOTALL)
    return match.group(1) if match else ""

# --- API Endpoint -----------------------------------------------------------

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_prompt(request: UserPromptRequest):
    """First, classifies the prompt. If it's finance-related, extracts key details."""
    # Standardized logging to English for consistency
    print(f"--- Analyzing prompt: {request.prompt[:80]}... ---")

    if not await is_finance_topic(request.prompt):
        print("--- Topic is not finance. Raising 400 error. ---")
        raise HTTPException(status_code=400, detail="I am specialized in generating presentations for the financial sector only.")

    print("--- Topic is finance. Extracting details... ---")
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
        response = await model.generate_content_async(extraction_prompt)
        json_string = extract_json_from_string(response.text)

        if not json_string:
            raise ValueError("Failed to extract JSON from AI response.")

        extracted_data = json.loads(json_string)
        print(f"--- Successfully parsed JSON: {extracted_data} ---")
        return AnalysisResult(**extracted_data)
    except Exception as e:
        print(f"--- CRITICAL ERROR during extraction: {e} ---")
        raw_response_text = "N/A"
        if 'response' in locals() and hasattr(response, 'text'):
            raw_response_text = response.text
        raise HTTPException(status_code=500, detail=f"Failed to extract details from prompt: {e}. Raw AI Response: {raw_response_text}")

