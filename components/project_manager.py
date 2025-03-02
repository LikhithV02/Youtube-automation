from pathlib import Path
from datetime import datetime
from logger import logger

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