from typing import List
from pydantic import BaseModel, Field

class Scenesandnarration(BaseModel):
    scene:str
    narration:str

class Scenes(BaseModel):
    scenes: List[Scenesandnarration] = Field(description="List of scenes and narrations")

class VideoMetadata(BaseModel):
    title: str = Field(description="Catchy and descriptive title for the video")
    description: str = Field(description="Engaging description of the video content")
    keywords: List[str] = Field(description="List of relevant keywords for the video")

class ImagePrompt(BaseModel):
    image_prompt: str = Field(description="Image prompt for the scene")

class VideoInfo(BaseModel):
    file_path: str
    title: str
    description: str
    keywords: List[str]
    category: str = "22"  # Default to "Entertainment" category
    privacy_status: str = "private"  # Default to private uploads

class Scene(BaseModel):
    description: str
    image_path: str
    narration: str
    audio_path: str
    start_time: float = 0
    duration: float = 0
    transition_duration: float = 1.0

    def set_timing(self, start_time: float, duration: float):
        self.start_time = start_time
        self.duration = duration