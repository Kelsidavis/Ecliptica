# animator.py
# Handles creation of animated GIFs or MP4 videos from image sequences for Ecliptica

import os
from PIL import Image
import imageio
from PIL import ImageDraw, ImageFont

def draw_timestamp_on_image(image, text):
    """
    Draws a timestamp text overlay on a given PIL image.
    """
    image = image.copy()
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()

    width, height = image.size
    margin = 10
    text_position = (margin, height - 30)

    draw.text(text_position, text, fill=255, font=font)

    return image

def save_gif(frames, output_path, duration=100):
    """
    Saves a list of PIL Image frames as an animated GIF.
    duration: Duration of each frame in milliseconds.
    """
    if not frames:
        raise ValueError("No frames provided to save_gif")

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0
    )

def save_mp4(frames, output_path, fps=10):
    """
    Saves a list of PIL Image frames as an MP4 video.
    fps: Frames per second for the output video.
    """
    import cv2
    import numpy as np

    if not frames:
        raise ValueError("No frames provided to save_mp4")

    # Convert PIL Images to numpy arrays
    frame_arrays = [cv2.cvtColor(np.array(frame), cv2.COLOR_GRAY2BGR) for frame in frames]

    height, width, _ = frame_arrays[0].shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for frame in frame_arrays:
        video.write(frame)

    video.release()
