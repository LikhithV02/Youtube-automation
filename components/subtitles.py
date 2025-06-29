from moviepy.editor import VideoClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from entity import Scene

def create_subtitle_clip(scene : Scene, frame_width, frame_height, font_size=64, font_path=r"fonts/Bangers-Regular.ttf"):
    words = scene.narration.split()
    word_positions = calculate_word_positions(words, font_size, font_path, frame_width, frame_height, position='center')
    animation_speed = scene.duration / len(words)
    def make_subtitle_frame(t):
        return create_subtitle_frame(t, words, word_positions, font_size, frame_width, frame_height, font_path, animation_speed)
    
    subtitle_clip = VideoClip(make_subtitle_frame, duration=scene.duration)
    subtitle_clip = subtitle_clip.set_position((0, 0)).set_mask(subtitle_clip.to_mask())

    return subtitle_clip

def calculate_word_positions(words, font_size, font_path, frame_width, frame_height, position='center'):
    font = ImageFont.truetype(font_path, font_size)
    line_height = int(font_size * 1.5)
    word_space = font_size // 2
    max_width = frame_width - 100  # 50px margin on each side
    
    lines = []
    current_line = []
    current_width = 0
    
    for word in words:
        word_width = font.getbbox(word)[2] - font.getbbox(word)[0]
        if current_width + word_width + word_space <= max_width or not current_line:
            current_line.append(word)
            current_width += word_width + word_space
        else:
            lines.append(current_line)
            current_line = [word]
            current_width = word_width + word_space
    
    if current_line:
        lines.append(current_line)
    
    total_height = len(lines) * line_height
    if position == 'bottom':
        start_y = frame_height - total_height - 50  # 50px from bottom
    elif position == 'center':
        start_y = (frame_height - total_height) // 2
    
    positions = []
    for i, line in enumerate(lines):
        current_x = 50  # Start with left margin
        for word in line:
            positions.append((current_x, start_y + i * line_height))
            word_width = font.getbbox(word)[2] - font.getbbox(word)[0]
            current_x += word_width + word_space
    
    return positions

def create_subtitle_frame(t, words, word_positions, font_size, frame_width, frame_height, font_path, animation_speed):
    # animation_speed = 200  # milliseconds per word
    current_word_index = int(t / animation_speed)
    frame = Image.new('RGBA', (frame_width, frame_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame)
    font = ImageFont.truetype(font_path, font_size)
    
    for i, (word, position) in enumerate(zip(words, word_positions)):
        is_current = i == current_word_index
        is_past = i < current_word_index
        
        if is_current:
            color = (255, 255, 0, 255)  # Yellow for current word
            font_size_current = font_size + 10
            font_current = ImageFont.truetype(font_path, font_size_current)
            draw.text(position, word, font=font_current, fill=color)
        elif is_past:
            color = (255, 255, 255, 255)  # White for past words
            draw.text(position, word, font=font, fill=color)
        else:
            color = (128, 128, 128, 128)  # Semi-transparent gray for future words
            draw.text(position, word, font=font, fill=color)
    
    rgb_frame = frame.convert('RGB')
    return np.array(rgb_frame)
   