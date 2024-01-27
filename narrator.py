import os
from openai import OpenAI
import base64
import json
import time
import simpleaudio as sa
import errno
import pygame
from elevenlabs import generate, play, set_api_key, voices

import cv2
import shutil
from PIL import Image
import numpy as np



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

client = OpenAI()

set_api_key(os.environ.get("ELEVENLABS_API_KEY"))
#define screen as global
screen = pygame.display.set_mode((640, 480))



def encode_image(image_path):
    while True:
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except IOError as e:
            if e.errno != errno.EACCES:
                # Not a "file in use" error, re-raise
                raise
            # File is being written to, wait a bit and retry
            time.sleep(0.1)


def play_audio(text, new=False):
    # display the image frame_0.jpg from frames directory

   
    
    
    #strip the [laugh] from the track
    playtext = text.replace("[LAUGH]","")
    if (new):
        audio = generate(playtext, voice=os.environ.get("SimonVoice"))
        unique_id = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8").rstrip("=")
        dir_path = os.path.join("narration", unique_id)
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, "audio.mp3")
        with open(file_path, "wb") as f:
            f.write(audio)
    else:
        file_path = ("assets/stop_slouching.mp3")

    
    
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    # if text contains [laugh] play laugh track# wait for audio to finish playing
    # while pygame.mixer.music.get_busy() == True:
      #  continue
 
    # while pygame.mixer.music.get_busy() == True:
      #  continue
    
    


def generate_new_line(base64_image):
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image"},
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{base64_image}",
                },
            ],
        },
    ]


def analyze_image(base64_image, script):
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "system",
                "content": """
                You are Sir David Attenborough. Narrate the picture of the human as if it is a nature documentary.
                Make it snarky and funny. Don't repeat yourself. Make it short. If I do anything remotely interesting, make a big deal about it! 
                If the person makes a funny face with the mouth wide open then add the code [LAUGH] to the response
                """,
            },
        ]
        + script
        + generate_new_line(base64_image),
        max_tokens=500,
    )
    response_text = response.choices[0].message.content
    return response_text

def capture_image(save):

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
        blitframe=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        #convert numpy.ndarry to pygame.surface 
        blitframe=np.rot90(blitframe)
        blitframe = pygame.surfarray.make_surface(blitframe)
        blitframe = pygame.transform.scale(blitframe, (640,480))
        screen.blit(blitframe, (0, 0, 640, 480))
        # Save the frame as an image file
        # every 5 seconds save a frame
        if (save):
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


def main():
    new = True
    win = False
    talking = False
    imageTime = 5
    victory = False
    prevTime = time.time()
    save = False
    
    script = []
    pygame.init()
    pygame.mixer.init()
    pygame.font.init()  # Initialize the font module
    font = pygame.font.SysFont('Arial', 50)  # Default font, size 25
  

    

    TALKING_END = pygame.USEREVENT+1
    pygame.mixer.music.set_endevent(TALKING_END)

    screen = pygame.display.set_mode((1280, 480))
    # while not exit - talking
    
    
    running = True
    
    while running:
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT:
                running = False
            #check space bar pressed
            if event.type == TALKING_END:
                print('talking end event')
                talking = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    print("Space bar pressed")
                    win = True
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r:
                    print("restart")
                    win = False
                    victory = False
        
        
                   
        
        
        #display countdown timer on screen
        #convert time to string
        timeString = str(imageTime-int((time.time() - prevTime)))
        if ((time.time() - prevTime) > imageTime):
            prevTime = time.time()
            save = True 
            
        if (not victory):
            capture_image(save)    
        save = False
        font = pygame.font.SysFont('Arial', 50)
        text_surface = font.render(timeString, True, (255, 0, 0))  # Red text
        screen.blit(text_surface, (320, 10))  # Draw text at position (50, 50)
        
        if (victory):
            font = pygame.font.SysFont('Arial', 150)
            text_surface = font.render("You Win!", True, (255, 0, 0))
            screen.blit(text_surface, (320, 50))
        
        pygame.display.flip()
        
        
        # if  victory

        
        # analyze posture
        if (not talking and not victory):
            print("👀 David is watching...")
            # path to your image
            image_path = os.path.join(os.getcwd(), "./frames/frame0.jpg")
             
            # getting the base64 encoding
            base64_image = encode_image(image_path)

            img = pygame.image.load('./frames/frame0.jpg')
            img = pygame.transform.scale(img, (640,480))
            screen.blit(img, (640, 0, 640, 480))
            pygame.display.flip()
       
        if (new and not victory):
            analysis = analyze_image(base64_image, script=script)
        else:
            if (win):
                analysis = "This is a test [LAUGH]"
            else:
                analysis = "You have not won yet."

        
        if (not talking and not victory):
            print("🎙️ David says:")
            print(analysis)
            talking = True
            play_audio(analysis,new)
            if "[LAUGH]" in analysis:
                victory = True
                laugh = pygame.mixer.Sound("assets/laugh.mp3")
                laugh.play()
        

        script = script + [{"role": "assistant", "content": analysis}]

        # wait for 5 seconds
        #time.sleep(2)


if __name__ == "__main__":
    main()




cap.release()
cv2.destroyAllWindows()