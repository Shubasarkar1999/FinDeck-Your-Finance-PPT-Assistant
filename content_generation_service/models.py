from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# --- Input Models ---

class AnalysisResultPayload(BaseModel):
    """
    The incoming request from the Streamlit frontend.
    It contains the refined topic and user choices.
    """
    topic: str
    target_audience: str
    slide_count: int
    theme: str
    language: str

# --- Output/Result Models ---

class Slide(BaseModel):
    """
    Defines the NEW structure for a single slide's content,
    matching the layout-driven format from the AI.
    """
    layout: str
    data: Dict[str, Any]
    # The image field is optional and will be added later by other services.
    image_base64: Optional[str] = None
    

class ContentResult(BaseModel):
    """
    The root object that the /generate-content endpoint returns.
    It's a list of the new, layout-aware Slide objects.
    """
    slides: List[Slide]
