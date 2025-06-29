import os
import requests
from dotenv import load_dotenv
load_dotenv()

def generate_audio(prompt: str, output_path: str):
    """
    Generate audio from text using ElevenLabs API and save to output_path.
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/JBFqnCBsd6RMkjVDRZzb?output_format=mp3_44100_128"
    headers = {
        "xi-api-key": os.getenv("ELEVEN_LABS_API_KEY"),
        "Content-Type": "application/json"
    }
    data = {
        "text": prompt,
        "model_id": "eleven_multilingual_v2"
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        raise Exception(f"Request failed with status {response.status_code}: {response.text}")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(response.content)

if __name__ == "__main__":
    generate_audio(
        "The first move is what sets everything in motion.",
        "output/test.mp3"
    )
