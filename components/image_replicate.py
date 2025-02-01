import replicate
import os

os.environ["REPLICATE_API_TOKEN"] = os.getenv("REPLICATE_API_KEY")

def generate_image(prompt: str, output_path:str, model:str="black-forest-labs/flux-schnell"):
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
    for index, item in enumerate(output):
        image_path = os.path.join(output_path, f"output_{index}.jpg")
        with open(image_path, "wb") as file:
            file.write(item.read())
