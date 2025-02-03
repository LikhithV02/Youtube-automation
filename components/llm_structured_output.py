from openai import OpenAI
import os
import json
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv
load_dotenv()

from langsmith.wrappers import wrap_openai

os.environ["LANGSMITH_TRACING"]="true"
os.environ["LANGSMITH_ENDPOINT"]="https://api.smith.langchain.com"
os.environ["LANGSMITH_API_KEY"]=os.getenv("LANGSMITH_API_KEY")
os.environ["LANGSMITH_PROJECT"]="youtube-automation"

client = wrap_openai(OpenAI(api_key=os.getenv("OPENAI_API_KEY")))

def generate_structured_output(prompt: str, output_format):
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "user", "content": prompt},
        ],
        response_format=output_format,
    )
    res = completion.choices[0].message.parsed
    return res.model_dump()

if __name__ == "__main__":
    # Generate scenes from a storyline
    prompt="Generate title, description and keywords for a video about Ironman"
    class VideoMetadata(BaseModel):
        title: str = Field(description="Catchy and descriptive title for the video")
        description: str = Field(description="Engaging description of the video content")
        keywords: List[str] = Field(description="List of relevant keywords for the video")
    res = generate_structured_output(prompt=prompt, output_format=VideoMetadata)
    print(res)
    print(type(res))