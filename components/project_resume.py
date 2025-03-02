import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from entity import VideoInfo, Scene
from components.project_manager import ProjectManager
from datetime import datetime
from logger import logger

class ProjectStateManager:
    """
    Manages project state to allow resuming interrupted projects.
    """
    def __init__(self, project_manager):
        self.project_manager = project_manager
        self.state_file = None
        self.current_state = {}
    
    def initialize_state_file(self):
        """
        Initialize the state file for the current project.
        """
        if not self.project_manager.current_project_dir:
            logger.error("No active project directory")
            return False
            
        self.state_file = self.project_manager.get_path("metadata", "project_state.json")
        
        # Initialize with empty state if file doesn't exist
        if not os.path.exists(self.state_file):
            self.current_state = {
                "topic": "",
                "storyline": "",
                "video_metadata": {},
                "scenes": [],
                "image_prompts": [],
                "processed_scenes": [],
                "status": "initialized",
                "last_updated": str(datetime.now())
            }
            self._save_state()
            logger.info(f"Initialized new state file at {self.state_file}")
        else:
            self.load_state()
            logger.info(f"Loaded existing state file from {self.state_file}")
            
        return True
    
    def load_state(self) -> Dict[str, Any]:
        """
        Load project state from the state file.
        """
        if not self.state_file or not os.path.exists(self.state_file):
            logger.error("State file does not exist")
            return {}
        
        try:
            with open(self.state_file, 'r') as f:
                self.current_state = json.load(f)
                return self.current_state
        except Exception as e:
            logger.error(f"Error loading state file: {str(e)}")
            return {}
    
    def _save_state(self):
        """
        Save current state to the state file.
        """
        try:
            # Update timestamp
            self.current_state["last_updated"] = str(datetime.now())
            
            with open(self.state_file, 'w') as f:
                json.dump(self.current_state, f, indent=2)
                
            logger.info(f"Saved project state to {self.state_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving state file: {str(e)}")
            return False
    
    def update_state(self, **kwargs):
        """
        Update specific fields in the state and save.
        """
        for key, value in kwargs.items():
            self.current_state[key] = value
        
        return self._save_state()
    
    def get_state_value(self, key, default=None):
        """
        Get a specific value from the state.
        """
        return self.current_state.get(key, default)
    
    def is_complete(self):
        """
        Check if the project is complete.
        """
        return self.current_state.get("status") == "complete"
    
    def mark_complete(self):
        """
        Mark the project as complete.
        """
        return self.update_state(status="complete")


def find_existing_project(base_dir: Union[str, Path], topic: str) -> Optional[Path]:
    """
    Find an existing project directory with the same topic name.
    
    Args:
        base_dir: Base directory to search in
        topic: Topic name to search for
        
    Returns:
        Path to existing project directory or None if not found
    """
    base_path = Path(base_dir)
    if not base_path.exists():
        return None
    
    # Format topic for comparison
    formatted_topic = topic.replace(' ', '_').lower()
    
    # First, try to find an exact match (without timestamp)
    exact_path = base_path / formatted_topic
    if exact_path.exists() and exact_path.is_dir():
        logger.info(f"Found exact topic match: {exact_path}")
        return exact_path
    
    # For backward compatibility, check timestamped directories
    # List all directories in the base directory
    for dir_path in base_path.iterdir():
        if dir_path.is_dir():
            # Check if the directory name is the exact topic
            if dir_path.name == formatted_topic:
                logger.info(f"Found exact topic match: {dir_path}")
                return dir_path
                
            # Check if it's a timestamped directory with our topic
            dir_name = dir_path.name
            if '_' in dir_name:
                # Extract the timestamp part (before the topic)
                parts = dir_name.split('_')
                if len(parts) >= 3:  # At least YYYYMMDD_HHMMSS_Topic
                    # Check if the first part looks like a timestamp (8 digits)
                    if parts[0].isdigit() and len(parts[0]) == 8:
                        # Extract everything after the timestamp_timestamp_ prefix
                        dir_topic = '_'.join(parts[2:])
                        
                        # Check if topic matches
                        if dir_topic == formatted_topic:
                            logger.info(f"Found timestamped topic match: {dir_path}")
                            return dir_path
    
    return None


def resume_or_create_project(base_dir: str, topic: str):
    """
    Check if a project exists and resume it, or create a new one.
    If project is complete with final video, return it immediately.
    
    Args:
        base_dir: Base directory for projects
        topic: Topic of the project
        
    Returns:
        tuple: (ProjectManager, ProjectStateManager, is_resumed, is_complete)
    """
    # Import ProjectManager from the main module
    from __main__ import ProjectManager
    
    # Find existing project
    existing_project = find_existing_project(base_dir, topic)
    project_manager = ProjectManager(base_dir)
    
    if existing_project:
        # Resume existing project
        logger.info(f"Found existing project at {existing_project}")
        project_manager.current_project_dir = existing_project
        
        # Check if final video exists
        video_path = existing_project / "video" / "final_video.mp4"
        if video_path.exists():
            logger.info(f"Found existing final video at {video_path}")
            
            # Initialize state manager
            state_manager = ProjectStateManager(project_manager)
            state_manager.initialize_state_file()
            
            # Mark as complete if not already
            if not state_manager.is_complete():
                state_manager.mark_complete()
                
            # Load video metadata if available
            metadata_path = existing_project / "metadata" / "video_info.json"
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list) and len(data) > 0:
                            logger.info("Successfully loaded existing video metadata")
                            # Return with is_complete flag set to True
                            return project_manager, state_manager, False, True
                except Exception as e:
                    logger.warning(f"Could not load video metadata: {str(e)}")
            
            # Return with is_complete flag even if metadata couldn't be loaded
            return project_manager, state_manager, False, True
        
        # Initialize state manager for non-complete projects
        state_manager = ProjectStateManager(project_manager)
        state_manager.initialize_state_file()
        
        if state_manager.is_complete():
            # Project is marked as complete in state but no video found
            # This suggests an inconsistency - create new project
            logger.info("Project marked complete but video not found. Creating new project instead.")
            project_manager.create_project_directory(topic)
            state_manager = ProjectStateManager(project_manager)
            state_manager.initialize_state_file()
            state_manager.update_state(topic=topic, status="initialized")
            return project_manager, state_manager, False, False
        else:
            logger.info(f"Resuming project from state: {state_manager.get_state_value('status')}")
            return project_manager, state_manager, True, False
    else:
        # Create new project
        logger.info(f"No existing project found for topic '{topic}'. Creating new project.")
        project_manager.create_project_directory(topic)
        
        # Initialize state manager
        state_manager = ProjectStateManager(project_manager)
        state_manager.initialize_state_file()
        state_manager.update_state(topic=topic, status="initialized")
        
        return project_manager, state_manager, False, False


def convert_scene_objects_to_dict(scenes: List[Scene]) -> List[Dict]:
    """
    Convert Scene objects to dictionaries for JSON serialization.
    """
    return [
        {
            "description": scene.description,
            "image_path": scene.image_path,
            "narration": scene.narration,
            "audio_path": scene.audio_path,
            "start_time": scene.start_time,
            "duration": scene.duration
        }
        for scene in scenes
    ]


def convert_dict_to_scene_objects(scene_dicts: List[Dict]) -> List[Scene]:
    """
    Convert dictionaries to Scene objects.
    """
    return [
        Scene(
            description=scene_dict.get("description", ""),
            image_path=scene_dict.get("image_path", ""),
            narration=scene_dict.get("narration", ""),
            audio_path=scene_dict.get("audio_path", ""),
            start_time=scene_dict.get("start_time", 0),
            duration=scene_dict.get("duration", 0)
        )
        for scene_dict in scene_dicts
    ]