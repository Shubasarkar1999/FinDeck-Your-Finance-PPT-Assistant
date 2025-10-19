from pydantic import BaseModel
from typing import List, Optional

# --- Pydantic models must match between services for communication ---

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

# Request received by this service
class ImageGenerationRequest(BaseModel):
    slides: List[Slide]
    theme: str = "professional"

# Response sent by this service
class ImageServiceResponse(BaseModel):
    slides_with_images: List[Slide]