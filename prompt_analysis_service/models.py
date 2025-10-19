from pydantic import BaseModel

class UserPromptRequest(BaseModel):
    prompt: str

class AnalysisResult(BaseModel):
    topic: str
    theme: str
    slide_count: int
    target_audience: str