import replicate
import os
from pathlib import Path

os.environ["REPLICATE_API_TOKEN"] = os.getenv("REPLICATE_API_KEY")

def generate_image(prompt: str, output_path:str, model:str="black-forest-labs/flux-schnell"):
    # Convert output_path to Path object for proper path handling
    output_path = Path(output_path)
    
    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output = replicate.run(
        model,
        input={
            "prompt": prompt,
            "go_fast": True,
            "megapixels": "1",
            "num_outputs": 1,
            "aspect_ratio": "9:16",
            "output_format": "jpg",
            "output_quality": 100,
            "num_inference_steps": 4
        },
        
    )
    # Save the first (and only) generated image directly to the specified path
    for item in output:
        with open(output_path, "wb") as file:
            file.write(item.read())
        break
