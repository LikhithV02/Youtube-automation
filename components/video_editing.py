import random
import os
from typing import List
from moviepy.editor import *
from moviepy.video.fx.all import resize
from PIL import Image
import numpy as np
from entity import Scene
from logger import logger
import traceback
from components.subtitles import create_subtitle_clip

def zoom_effect(clip, zoom_type='in', zoom_ratio=0.15, initial_zoom=1.5):
    """
    Apply a zoom effect to a video clip.
    
    Parameters:
    - clip: The video clip to which the zoom effect will be applied.
    - zoom_type: The type of zoom effect ('in' or 'out').
    - zoom_ratio: The ratio by which the zoom will increase or decrease.
    - initial_zoom: The initial zoom level for the 'out' zoom type.
    
    Returns:
    - A video clip with the zoom effect applied.
    """
    logger.info(f"Applying zoom effect: type={zoom_type}, ratio={zoom_ratio}, initial_zoom={initial_zoom}")
    
    def zoom(get_frame, t):
        try:
            img = Image.fromarray(get_frame(t))
            original_size = img.size

            if zoom_type == 'in':
                scale = 1 + t * zoom_ratio
            elif zoom_type == 'out':
                scale = initial_zoom - t * (initial_zoom - 1) * zoom_ratio
            else:
                scale = 1

            # Calculate the size to which we need to scale the image
            scaled_size = (int(original_size[0] * scale), int(original_size[1] * scale))
            
            # Resize the image
            img = img.resize(scaled_size, Image.LANCZOS)
            
            # Calculate cropping coordinates to get back to original size
            left = (scaled_size[0] - original_size[0]) // 2
            top = (scaled_size[1] - original_size[1]) // 2
            right = left + original_size[0]
            bottom = top + original_size[1]
            
            # Crop the image to the original size
            img = img.crop((left, top, right, bottom))
            
            return np.array(img)
        except Exception as e:
            logger.error(f"Error applying zoom effect at time {t}: {e}")
            logger.debug(traceback.format_exc())
            return get_frame(t)  # Return the original frame in case of error

    return clip.fl(zoom)

def apply_random_transition(clip, duration):
    transitions = ['crossfade', 'fade']
    transition = random.choice(transitions)
    
    if transition == 'crossfade':
        return clip.crossfadein(duration)
    elif transition == 'fade':
        return clip.fadein(duration)
    
    return clip

def get_video_dimensions(image_path: str):
    """
    Get the dimensions of an image file, which will be used as the video dimensions.
    
    Args:
    image_path (str): Path to the image file.
    
    Returns:
    tuple: A tuple containing the width and height of the image.
    """
    try:
        with Image.open(image_path) as img:
            return img.size
    except IOError:
        print(f"Error: Unable to open image file {image_path}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def choose_bg_music(music_folder: str, required_duration: float):
    """
    Choose background music and loop/trim it to match required duration
    
    Args:
    music_folder (str): Path to music folder
    required_duration (float): Required duration in seconds
    
    Returns:
    AudioFileClip: Audio clip matching the required duration
    """
    # List all files in the folder
    music_files = [f for f in os.listdir(music_folder) if os.path.isfile(os.path.join(music_folder, f))]
    
    if not music_files:
        raise ValueError(f"No music files found in {music_folder}")

    # Choose a random file
    chosen_file = random.choice(music_files)
    chosen_file_path = os.path.join(music_folder, chosen_file)
    
    # Load the audio file
    bg_music = AudioFileClip(chosen_file_path)
    
    # If music is shorter than required duration, loop it
    if bg_music.duration < required_duration:
        num_loops = int(np.ceil(required_duration / bg_music.duration))
        bg_music = vfx.loop(bg_music, n=num_loops)
    
    # Trim to exact duration needed
    bg_music = bg_music.subclip(0, required_duration)
    bg_music = bg_music.volumex(0.2)
    
    return bg_music

def create_advanced_video(scenes: List[Scene], output_path: str, fps: int = 24):
    try:
        video_clips = []
        audio_clips = []
        subtitle_clips = []
        frame_width, frame_height = get_video_dimensions(scenes[0].image_path)
        if frame_width is None or frame_height is None:
            logger.error("Error: Could not determine video dimensions. Using default 1080p.")
            frame_width, frame_height = 1920, 1080

        current_time = 0
        for scene in scenes:
            try:
                logger.info(f"Processing scene: {scene.description}")

                # Create image clip
                img_clip = ImageClip(scene.image_path).set_duration(scene.duration)
                logger.info(f"Created image clip for {scene.image_path} with duration {scene.duration}")

                # Apply zoom effect
                img_clip = zoom_effect(img_clip, 'in' if len(video_clips) % 2 == 0 else 'out')
                logger.info(f"Applied zoom effect to image clip")

                # Add transition effect
                if len(video_clips) > 0:
                    img_clip = apply_random_transition(img_clip, scene.transition_duration)
                    logger.info(f"Applied transition effect with duration {scene.transition_duration}")

                # Set start and end times
                img_clip = img_clip.set_start(current_time).set_end(current_time + scene.duration)
                logger.info(f"Set start time to {current_time} and end time to {current_time + scene.duration} for image clip")

                # Create audio clip
                audio_clip = AudioFileClip(scene.audio_path).set_start(current_time)
                logger.info(f"Created audio clip for {scene.audio_path} starting at {current_time}")

                # Create subtitle clip
                subtitle_clip = create_subtitle_clip(scene, frame_width, frame_height)
                subtitle_clip = subtitle_clip.set_start(current_time)
                logger.info(f"Created subtitle clip starting at {current_time}")

                video_clips.append(img_clip)
                audio_clips.append(audio_clip)
                if subtitle_clip is not None:
                    subtitle_clips.append(subtitle_clip)

                current_time += scene.duration
                logger.info(f"Updated current time to {current_time}")

            except Exception as e:
                logger.error(f"Error processing scene: {scene.description}, {e}")
                logger.debug(traceback.format_exc())
                continue

        if not video_clips:
            raise ValueError("No valid video clips were created")

        # Get background music matching the total video duration
        musics_folder = r'E:\Projects\Youtube-automation\bg_musics'
        bg_music = choose_bg_music(musics_folder, current_time)
        logger.info(f"Selected and processed background music from {musics_folder}")

        # Combine all clips
        final_video = CompositeVideoClip(video_clips + subtitle_clips)
        final_audio = CompositeAudioClip([bg_music] + audio_clips)
        final_clip = final_video.set_audio(final_audio)
        
        # Write output video
        final_clip.write_videofile(output_path, fps=fps, codec="h264_nvenc")
        
        # Clean up
        final_clip.close()
        final_video.close()
        final_audio.close()
        bg_music.close()
        for clip in video_clips + audio_clips + subtitle_clips:
            if clip is not None:
                clip.close()
                
        return output_path

    except Exception as e:
        logger.error(f"Error in create_advanced_video: {str(e)}")
        logger.debug(traceback.format_exc())
        raise
