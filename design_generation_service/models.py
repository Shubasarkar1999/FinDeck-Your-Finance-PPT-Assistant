# models.py

from pydantic import BaseModel
from typing import List, Optional

# --- Models for internal data structure ---
class SlideData(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    items: Optional[List[str]] = None
    points: Optional[List[str]] = None
    message: Optional[str] = None

class Slide(BaseModel):
    layout: str
    data: SlideData
    image_base64: Optional[str] = None

# --- Models for API communication ---
class GenerationRequest(BaseModel):
    slides: List[Slide]
    theme: str # ✅ NEW: Field to specify the chosen theme identifier

class ImageServiceRequest(BaseModel):
    slides: List[Slide]

class GenerationResponse(BaseModel):
    download_url: str
    preview_url: str