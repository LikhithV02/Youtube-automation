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
"""

video_metadata_template = """
You are a digital content strategist specializing in creating engaging metadata for videos. Given a storyline and the theme of the video, create a compelling title, description, and list of keywords that will help the video perform well on social media and video platforms.

Storyline: {storyline}
Theme: {theme}

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
"""