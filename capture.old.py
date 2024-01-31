import cv2
import time
import os
import shutil
from PIL import Image
import numpy as np
import os

# Folder
folder = "frames"

# Create the frames folder if it doesn't exist
frames_dir = os.path.join(os.getcwd(), folder)
os.makedirs(frames_dir, exist_ok=True)

# Initialize the webcam
cap = cv2.VideoCapture(3)

# Check if the webcam is opened correctly
if not cap.isOpened():
    raise IOError("Cannot open webcam")

# Wait for the camera to initialize and adjust light levels
time.sleep(2)

while True:
    ret, frame = cap.read()
    if ret:
        # Convert the frame to a PIL image
        pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        # Resize the image
        max_size = 250
        max_cache = 5
        ratio = max_size / max(pil_img.size)
        new_size = tuple([int(x*ratio) for x in pil_img.size])
        resized_img = pil_img.resize(new_size, Image.LANCZOS)

        # Convert the PIL image back to an OpenCV image
        frame = cv2.cvtColor(np.array(resized_img), cv2.COLOR_RGB2BGR)

        # Save the frame as an image file
        print("📸 Say cheese! Saving frame.")
        path = f"{folder}/frame0.jpg"
        #copy a frame on disk to save as a previous frame
        if os.path.exists(path):
            if os.path.exists(f"{folder}/frame{max_cache}.jpg"):
                os.remove(f"{folder}/frame{max_cache}.jpg")
            for i in range(max_cache-1,-1,-1):
                shutil.copy(f"{folder}/frame{i}.jpg",f"{folder}/frame{i+1}.jpg")
        cv2.imwrite(path, frame)
    else:
        print("Failed to capture image")

    # Wait for 2 seconds
    time.sleep(5)

# Release the camera and close all windows
cap.release()
cv2.destroyAllWindows()
