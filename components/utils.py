from entity import VideoInfo
import json

def save_video_info(video_info: VideoInfo, filename: str = "video_info.json"):
    """
    Save VideoInfo object to a JSON file.
    If the file exists, it appends the new info to the existing data.
    """
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = []
    
    data.append(video_info.model_dump())
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)