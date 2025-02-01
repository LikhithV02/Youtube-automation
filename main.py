from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
# from langchain_core.pydantic_v1 import BaseModel, Field
from pydantic import BaseModel, Field
import random
import time
from image_downloader import generate_image_pixart, generate_image_firework, generate_image_replicate
from langchain import hub
from langchain_community.agent_toolkits.load_tools import load_tools
from langchain.agents import AgentExecutor, create_react_agent
from typing import List
from video_editing import create_advanced_video
from langchain_core.exceptions import OutputParserException
from elevenlabs import VoiceSettings, play, save
from elevenlabs.client import ElevenLabs
import uuid
from moviepy.editor import *
from Narration_generator import generate_narrations
# from test8 import apply_subtitles
from gtts import gTTS
from scene import Scene
import os
from video_info import VideoInfo, load_video_info, save_video_info
from dotenv import load_dotenv
load_dotenv()
# Initialize the Groq LLM
groq_llm = ChatGroq(api_key=os.getenv('GROQ_API_KEY'), model="llama3-70b-8192")

tools = load_tools(["ddg-search"])
prompt = hub.pull("hwchase17/react")
agent = create_react_agent(groq_llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True, )

class Scenesandnarration(BaseModel):
    scene:str
    narration:str

class Scenes(BaseModel):
    scenes: List[Scenesandnarration] = Field(description="List of scenes and narrations")

class VideoMetadata(BaseModel):
    title: str = Field(description="Catchy and descriptive title for the video")
    description: str = Field(description="Engaging description of the video content")
    keywords: List[str] = Field(description="List of relevant keywords for the video")

class Image_prompt(BaseModel):
    image_prompt: str = Field(description="Image prompt for the scene")

image_prompt_parser = JsonOutputParser(pydantic_object=Image_prompt)
scenes_parser = JsonOutputParser(pydantic_object=Scenes)
video_metadata_parser = JsonOutputParser(pydantic_object=VideoMetadata)

# Define a prompt template for generating scenes
scenes_template = """
You are a video content creator specializing in breaking down topics into engaging video scenes with narration. Given a topic and the content provided by an AI research agent, create a list of scenes with narration that capture the essence of the content while following a standard video structure. The number of scenes should be appropriate for the content, typically ranging from 4 to 5 scenes.

Topic: {topic}
Content: {storyline}

Create a list of scenes with narration that includes:
1. An introduction scene with narration setting up the video's theme
2. Multiple content scenes with narration covering the main points
3. A conclusion scene with narration summarizing key takeaways
4. An outro scene with narration with a call-to-action

Each scene should be a brief description (2-3 sentences) that sets up a clear visual moment or action. Ensure the scenes flow logically and maintain viewer engagement throughout the video.
Each narration should be concise, short (20-25 words) and should be like narrating the story.

Provide the scenes in the following format:
{{
  "scenes": [
    {{
      "scene": "Description of the first scene",
      "narration": "Narration for the first scene"
    }},
    {{
      "scene": "Description of the second scene",
      "narration": "Narration for the second scene"
    }},
    ...
  ]
}}

{format_instructions}
"""

video_metadata_template = """
You are a digital content strategist specializing in creating engaging metadata for videos. Given a storyline and the theme of the video, create a compelling title, description, and list of keywords that will help the video perform well on social media and video platforms.

Storyline: {storyline}
Theme: {theme}

Provide the video metadata in the following format:

{format_instructions}

Ensure the title is catchy and under 100 characters, the description is engaging and between 100-500 characters, and include 5-10 relevant keywords.
"""

# Define a prompt template for generating image prompts
image_prompt_template = """
You are a cinematographer creating concise image prompts for cinematic scenes and specializing in visual storytelling and cinematic narrative design. Your role is to help create compelling visual narratives that can be translated into a series of AI-generated images for video production. You have deep knowledge of cinematography, visual storytelling techniques, and narrative structure. For each scene description, generate a brief but evocative image prompt that includes:

1. A key visual element (e.g., camera angle, lighting style)
2. The overall mood or atmosphere
3. A notable cinematic technique or style reference

Previous Scene Description: {previous_scene}
Previous Image Prompt: {previous_prompt}
Current Scene: {scene_description}

Keep the prompt to 1-2 sentences, focusing on the most impactful visual aspects that capture the scene's essence. Ensure that your prompt connects visually and thematically with the previous scene's description and prompt when provided.

Your response should be in the following JSON format:
{{
    "image_prompt": "Your image prompt here"
}}

{format_instructions}
"""

image_prompt = PromptTemplate(
    template=image_prompt_template, 
    input_variables=["previous_scene", "previous_prompt", "scene_description"],
    partial_variables={"format_instructions": image_prompt_parser.get_format_instructions()},
)

scenes_prompt = PromptTemplate(
    template=scenes_template,
    input_variables=["storyline","topic" ],
    partial_variables={"format_instructions": scenes_parser.get_format_instructions()},
)

video_metadata_prompt = PromptTemplate(
    template=video_metadata_template,
    input_variables=["storyline", "theme"],
    partial_variables={"format_instructions": video_metadata_parser.get_format_instructions()},
)
# Function to generate scenes from a storyline
def generate_scenes_from_storyline(storyline, topic):
    chain = scenes_prompt | groq_llm | scenes_parser
    res = chain.invoke({"storyline": storyline, 'topic':topic})
    print(res)
    return res.get('scenes', [])

def generate_video_metadata(storyline: str, theme: str):
    chain = video_metadata_prompt | groq_llm | video_metadata_parser
    res = chain.invoke({"storyline": storyline, "theme": theme})
    # print(res)
    return res

# Function to generate cinematic image prompts for a series of scenes
def generate_cinematic_image_prompts(scenes):
    prompts = []
    previous_scene = ""
    previous_prompt = ""
    
    for scene in scenes:
        chain = image_prompt | groq_llm | image_prompt_parser
        try:
            res = chain.invoke({
                "previous_scene": previous_scene,
                "previous_prompt": previous_prompt,
                "scene_description": scene.get('scene')
            })
            prompt = res.get('image_prompt')
        except OutputParserException as e:
            # If parsing fails, use the raw output as the prompt
            prompt = str(e.llm_output).strip()

        prompts.append(prompt)
        
        previous_scene = scene.get('scene')
        previous_prompt = prompt

    return prompts

def text_to_speech(narration: str, audio_path: str):
    tts = gTTS(text=narration, lang='en')
    tts.save(audio_path)

    # client = ElevenLabs(
    #     api_key="0644e6d0e5d54006dbca1a4c6eb297f4",
    # )
    # audio = client.text_to_speech.convert(
    #     voice_id="pNInz6obpgDQGcFmaJgB",
    #     optimize_streaming_latency="0",
    #     output_format="mp3_22050_32",
    #     text=narration,
    #     voice_settings=VoiceSettings(
    #         stability=0.1,
    #         similarity_boost=0.3,
    #         style=0.2,
    #     ),
    # )

    # save(audio, audio_path)


def custom_round( x: float, threshold: float = 0.5) -> int:
    # Determine the integer part of the number
    integer_part = int(x)
    
    # Determine the fractional part
    fractional_part = x - integer_part
    
    # Round based on the threshold
    if fractional_part < threshold:
        return integer_part
    else:
        return integer_part + 1
    
def get_audio_duration(audio_path: str):
    clip = AudioFileClip(audio_path)
    sing_audio = clip.duration
    sing_audio = custom_round(sing_audio)
    return sing_audio

# Main function to process a storyline
def process_storyline(storyline, inp):
    # Generate scenes from the storyline
    video_metadata = generate_video_metadata(storyline, inp)
    print("Generated Video Metadata:")
    print(f"Title: {video_metadata.get('title')}")
    print(f"Description: {video_metadata.get('description')}")
    print(f"Keywords: {', '.join(video_metadata.get('keywords'))}")
    print()
    scenes = []
    scene_descriptions = generate_scenes_from_storyline(storyline, inp)
    print("Generated Scenes:")
    for i, scene in enumerate(scene_descriptions):
        # print(scene)``
        print(f"Scene {i+1}: {scene.get('scene')}")
        print(f"narration {i+1}: {scene.get('narration')}")
    print()

    # Generate cinematic image prompts for the scenes
    image_prompts = generate_cinematic_image_prompts(scene_descriptions)
    current_time = 0
    # Print the prompts and generate images
    for i, (scene_description, image_prompt) in enumerate(zip(scene_descriptions, image_prompts)):
        
        image_path = f"image_{i}.jpg"
        images_dir = 'home/asi/GenAI/output'
        os.makedirs(images_dir, exist_ok=True)
        image_path = os.path.join('output', image_path)
        generate_image_pixart(image_prompt, image_path)

        # narration = generate_narrations(scene_description)
        audio_path = f"narration_{i}.mp3" 
        narration_dir = "narrations"
        os.makedirs(narration_dir, exist_ok=True)
        audio_path = os.path.join(narration_dir, audio_path)
        text_to_speech(scene_description.get('narration'), audio_path)

        audio_duration = get_audio_duration(audio_path)

        scene = Scene(
            description=scene_description.get('scene'),
            image_path=image_path,
            narration=scene_description.get('narration'),
            audio_path=audio_path,
            start_time=current_time,
            duration=audio_duration
        )

        print(f"Scene {i+1}:")
        print(f"Description: {scene.description}")
        print(f"Cinematic Image Prompt: {image_prompt}")
        print(f"Narration: {scene.narration}")

        scenes.append(scene)
        
        current_time += audio_duration
        print()

    uniq_id = uuid.uuid4()
    output_folder = "generated_videos"
    os.makedirs(output_folder, exist_ok=True)
    video_name = f"output_advanced_video_{uniq_id}.mp4"
    video_path = os.path.join(output_folder, video_name)
    create_advanced_video(scenes, video_path)

    video_info = VideoInfo(
        file_path=video_path,
        title=video_metadata.get('title'),
        description=video_metadata.get('description'),
        keywords=video_metadata.get('keywords'),
    )

    return video_info

def create_video_with_retry(inp: str, retries: int = 5, backoff_factor: float = 1.0, max_delay: int = 60):
    delay = backoff_factor  # initial delay in seconds
    
    for attempt in range(retries):
        try:
            # Step 1: Generate the storyline
            storyline = agent_executor.invoke({"input": inp})
            
            # Step 2: Process the storyline to create video information
            video_info = process_storyline(storyline["output"], inp)

            # Step 3: Output video information
            print(f"Video created: {video_info.file_path}")
            print(f"Video Title: {video_info.title}")
            print(f"Video Description: {video_info.description}")
            print(f"Video Keywords: {', '.join(video_info.keywords)}")

            # Step 4: Save video information to a file
            save_video_info(video_info)
            print(f"Video info saved to video_info.json")

            # If everything works, return the video info
            return video_info

        except Exception as e:
            print(f"Error: {e}")

            if attempt < retries - 1:
                # Exponential backoff with jitter
                sleep_time = delay + random.uniform(0, 1)
                print(f"Retrying in {sleep_time:.2f} seconds... (Attempt {attempt + 1} of {retries})")
                time.sleep(sleep_time)
                delay = min(max_delay, delay * 2)  # Exponentially increase delay
            else:
                print("Max retries reached. Exiting...")
                raise e  # Reraise the exception after max retries

if __name__ == "__main__":
    inp = "Iron-Man story"
    create_video_with_retry(inp=inp)

