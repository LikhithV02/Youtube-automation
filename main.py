from moviepy.editor import *
from typing import List
from typing import Optional
import random
import time
import os
import uuid
from datetime import datetime
from pathlib import Path

from components.web_research_agent import web_search_agent
from components.llm_structured_output import generate_structured_output
from components.image_replicate import generate_image
from components.audio import generate_audio
from constants import scenes_template, video_metadata_template, image_prompt_template
from entity import Scenes, VideoMetadata, ImagePrompt, VideoInfo, Scene
from components.video_editing import create_advanced_video
from components.utils import save_video_info
from logger import logger

from dotenv import load_dotenv
load_dotenv()

class ProjectManager:
    def __init__(self, base_dir="projects"):
        self.base_dir = Path(base_dir)
        self.current_project_dir = None

    def create_project_directory(self, topic: str) -> Path:
        """Create a new project directory with timestamp and topic name"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = f"{timestamp}_{topic.replace(' ', '_')}"
        project_dir = self.base_dir / project_name
        
        # Create project structure
        subdirs = ["images", "audio", "video", "metadata"]
        project_dir.mkdir(parents=True, exist_ok=True)
        for subdir in subdirs:
            (project_dir / subdir).mkdir(exist_ok=True)
            
        self.current_project_dir = project_dir
        logger.info(f"Created project directory: {project_dir}")
        return project_dir

    def get_path(self, file_type: str, filename: str) -> Path:
        """Get the appropriate path for a file based on its type"""
        if not self.current_project_dir:
            logger.error("No active project directory")
            return
            
        type_dir_map = {
            "image": "images",
            "audio": "audio",
            "video": "video",
            "metadata": "metadata"
        }
        
        if file_type not in type_dir_map:
            raise ValueError(f"Invalid file type: {file_type}")
            
        return self.current_project_dir / type_dir_map[file_type] / filename

# Function to generate scenes from a storyline
def generate_scenes_from_storyline(project_manager: ProjectManager, storyline: str, topic: str) -> List[dict]:
    """Generate scenes with error handling"""
    try:
        scenes_prompt = scenes_template.format(topic=topic, storyline=storyline)
        res = generate_structured_output(prompt=scenes_prompt, output_format=Scenes)
        logger.info(f"Generated {len(res.get('scenes', []))} scenes")
        return res.get('scenes', [])
    except Exception as e:
        logger.error(f"Error generating scenes: {str(e)}")

def generate_video_metadata(project_manager: ProjectManager, storyline: str, theme: str) -> dict:
    """Generate video metadata with error handling"""
    try:
        video_metadata_prompt = video_metadata_template.format(storyline=storyline, theme=theme)
        res = generate_structured_output(prompt=video_metadata_prompt, output_format=VideoMetadata)
        logger.info("Generated video metadata")
        return res
    except Exception as e:
        logger.error(f"Error generating video metadata: {str(e)}")

# Function to generate cinematic image prompts for a series of scenes
def generate_cinematic_image_prompts(scenes):
    """Generate cinematic image prompts for a series of scenes with error handling and logging."""
    prompts = []
    previous_scene = ""
    previous_prompt = ""
    
    try:
        for scene in scenes:
            image_prompt = image_prompt_template.format(
                                                        previous_scene=previous_scene,
                                                        previous_prompt=previous_prompt,
                                                        scene_description=scene.get('scene')
                                                        )
            res = generate_structured_output(prompt=image_prompt, output_format=ImagePrompt)

            prompts.append(res.get('image_prompt'))
            
            previous_scene = scene.get('scene')
            previous_prompt = res.get('image_prompt')
            
        logger.info(f"Successfully generated {len(prompts)} image prompts")
        return prompts
    except Exception as e:
        logger.error(f"Error in generate_cinematic_image_prompts: {str(e)}")

def custom_round(x: float, threshold: float = 0.5) -> int:
    """
    Round a number based on a threshold.
    """
    integer_part = int(x)
    fractional_part = x - integer_part
    
    return integer_part + (1 if fractional_part >= threshold else 0)
    
def get_audio_duration(audio_path: str, max_retries: int = 3, retry_delay: float = 1.0) -> Optional[int]:
    """
    Get the duration of an audio file with robust error handling and retries.
    """
    path = Path(audio_path)
    
    # Check if file exists
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    # Check file permissions
    if not os.access(path, os.R_OK):
        # Try to fix permissions
        try:
            os.chmod(path, 0o644)  # Read/write for owner, read for others
        except Exception as e:
            raise PermissionError(f"Cannot read audio file due to permissions: {audio_path}. Error: {str(e)}")
    
    # Retry loop
    for attempt in range(max_retries):
        try:
            clip = AudioFileClip(str(path))
            duration = clip.duration
            
            # Properly close the clip to release the file handle
            clip.close()
            
            # Round to nearest integer
            return int(round(duration))
            
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                raise Exception(f"Failed to get audio duration after {max_retries} attempts: {str(e)}")
    
    return None

# Main function to process a storyline
def process_storyline(project_manager: ProjectManager, storyline: str, topic: str) -> VideoInfo:
    """Process storyline with comprehensive error handling and file management"""
    try:
        # Generate video metadata
        video_metadata = generate_video_metadata(project_manager, storyline, topic)
        logger.info(f"Generated video metadata: {video_metadata.get('title')}")

        # Generate and process scenes
        scenes = []
        scene_descriptions = generate_scenes_from_storyline(project_manager, storyline, topic)
        image_prompts = generate_cinematic_image_prompts(scene_descriptions)
        
        current_time = 0
        for i, (scene_description, image_prompt) in enumerate(zip(scene_descriptions, image_prompts)):
            try:
                # Generate and save image
                image_filename = f"scene_{i+1}.jpg"
                image_path = project_manager.get_path("image", image_filename)
                generate_image(image_prompt, str(image_path))
                logger.info(f"Generated image for scene {i+1}")

                # Generate and save audio
                audio_filename = f"narration_{i+1}.mp3"
                audio_path = project_manager.get_path("audio", audio_filename)
                generate_audio(scene_description.get('narration'), str(audio_path))
                logger.info(f"Generated audio for scene {i+1}")

                # Get audio duration
                audio_duration = get_audio_duration(str(audio_path))

                # Create scene object
                scene = Scene(
                    description=scene_description.get('scene'),
                    image_path=str(image_path),
                    narration=scene_description.get('narration'),
                    audio_path=str(audio_path),
                    start_time=current_time,
                    duration=audio_duration
                )
                scenes.append(scene)
                current_time += audio_duration

            except Exception as e:
                logger.error(f"Error processing scene {i+1}: {str(e)}")

        # Create final video
        video_filename = f"final_video.mp4"
        video_path = project_manager.get_path("video", video_filename)
        create_advanced_video(scenes, str(video_path))
        logger.info("Created final video")

        # Create video info
        video_info = VideoInfo(
            file_path=str(video_path),
            title=video_metadata.get('title'),
            description=video_metadata.get('description'),
            keywords=video_metadata.get('keywords'),
        )

        # Save video info
        metadata_path = project_manager.get_path("metadata", "video_info.json")
        save_video_info(video_info, str(metadata_path))
        logger.info("Saved video information")

        return video_info

    except Exception as e:
        logger.error(f"Error in process_storyline: {str(e)}")

def create_video_with_retry(topic: str, retries: int = 5, backoff_factor: float = 1.0, max_delay: int = 60) -> VideoInfo:
    """Create video with retry mechanism and error handling"""
    project_manager = ProjectManager()
    project_dir = project_manager.create_project_directory(topic)
    delay = backoff_factor

    for attempt in range(retries):
        try:
            # Generate storyline
            storyline = web_search_agent(topic)
            logger.info("Generated storyline")

            # Process storyline and create video
            video_info = process_storyline(project_manager, storyline, topic)
            logger.info(f"Successfully created video: {video_info.file_path}")
            return video_info

        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {str(e)}")

            if attempt < retries - 1:
                sleep_time = delay + random.uniform(0, 1)
                logger.info(f"Retrying in {sleep_time:.2f} seconds... (Attempt {attempt + 1} of {retries})")
                time.sleep(sleep_time)
                delay = min(max_delay, delay * 2)
            else:
                logger.error("Max retries reached. Exiting...")

if __name__ == "__main__":
    try:
        topic = "Wonder women story"
        video_info = create_video_with_retry(topic=topic)
        logger.info(f"Successfully created video: {video_info.file_path}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

