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
import asyncio
import pathlib
import textwrap
import google.generativeai as genai
import configparser

from IPython.display import display
from IPython.display import Markdown

from googlegen import generation_config, safety_settings


CONFIG_FILE = 'config.ini'

def list_available_webcams(max_webcams=10):
    """ List available webcams """
    available_webcams = []
    for i in range(max_webcams):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_webcams.append(i)
            cap.release()
    return available_webcams

def select_webcam():
    """ Let user select a webcam """
    webcams = list_available_webcams()
    if not webcams:
        raise IOError("No webcams available")
    
    print("Available webcams:")
    for i, cam in enumerate(webcams):
        print(f"{i}: Webcam {cam}")
    
    while True:
        try:
            choice = int(input(f"Select a webcam (0-{len(webcams)-1}): "))
            if 0 <= choice < len(webcams):
                return webcams[choice]
            else:
                print(f"Please enter a number between 0 and {len(webcams)-1}")
        except ValueError:
            print("Invalid input, please enter a number")



# Folder
folder = "frames"

# Create the frames folder if it doesn't exist
frames_dir = os.path.join(os.getcwd(), folder)
os.makedirs(frames_dir, exist_ok=True)



     

class Settings:
    def __init__(self, webcam=None, chatGPT=False, Google=False, ElevenLabs=False, auto=False):
        self.webcam = webcam
        self.chatGPT = chatGPT
        self.Google = Google
        self.ElevenLabs = ElevenLabs
        self.auto = auto

    def save(self):
        config = configparser.ConfigParser()
        config['Settings'] = {
            'Webcam': str(self.webcam) if self.webcam is not None else '',
            'ChatGPT': str(self.chatGPT),
            'Google': str(self.Google),
            'ElevenLabs': str(self.ElevenLabs),
            'Auto': str(self.auto)
        }
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)

    def load(self):
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        if 'Settings' in config:
            self.webcam = int(config['Settings'].get('Webcam', '')) if config['Settings'].get('Webcam', '').isdigit() else None
            self.chatGPT = config.getboolean('Settings', 'ChatGPT', fallback=False)
            self.Google = config.getboolean('Settings', 'Google', fallback=False)
            self.ElevenLabs = config.getboolean('Settings', 'ElevenLabs', fallback=False)
            self.auto = config.getboolean('Settings', 'Auto', fallback=False)



def to_markdown(text):
  text = text.replace('•', '  *')
  return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))


# Thread safe file read
def encode_image(image_path,scale_factor=0.5):
    while True:
        try:
            with open(image_path, "rb") as image_file:
            # Load the image
                image = cv2.imread(image_path)
                
                # Get original dimensions
                original_height, original_width = image.shape[:2]
                
                # Calculate new dimensions
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                new_size = (new_width, new_height)
                
                # Resize the image
                resized_image = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
                
                # Encode the image to a memory buffer
                _, buffer = cv2.imencode('.jpg', resized_image, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                
                # Convert buffer to base64 string
                return base64.b64encode(buffer).decode('utf-8')
            # return base64.b64encode(image_file.read()).decode("utf-8")
        except IOError as e:
            if e.errno != errno.EACCES:
                # Not a "file in use" error, re-raise
                raise
            # File is being written to, wait a bit and retry
            time.sleep(0.1)


# Play audio if var new is true then generate new audio from elevenlabs
def play_audio(text, new=False):
    #strip the [laugh] from the track audio
    playtext = text.replace("[LAUGH]","")
    if (new):
        # audio = generate(playtext, voice=os.environ.get("SimonVoice"))
        audio = generate(playtext, voice="gMy4qOvdI8GLfASRvYgY")
        unique_id = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8").rstrip("=")
        dir_path = os.path.join("narration", unique_id)
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, "audio.mp3")
        with open(file_path, "wb") as f:
            f.write(audio)
    else:
        file_path = ("assets/stop_slouching.mp3")
        # file_path = ("assets/magnificent.mp3")
    
    
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()

    

# user command sent to ChatGPT
def generate_ChatGPT_prompt(base64_image):
    # print the size of the base64 image
    
    print ("Generating ChatGPT prompt",np.size(base64_image)," ",type(base64_image))
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image in 100 words or fewer. Make it sound like David Attenborugh.  Emphasize the humourous things that the people in the scene are doing.  ONLY if the scene Rediculously funny return the word [LAUGH] in the response. Do not say [LAUGH] if the original scene is not rediculous"},
                {
                    "type": "image_url",
                    "image_url": { 
                        "url": f"data:image/jpeg;base64,{base64_image}",
                        "detail": "low"
                    },
                },
            ],
        },
    ]


# Chat GPT custom instruction for the image analyser
def custom_instructions_ChatGPT(base64_image, script):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """
    You are David Attenbourgh. Describe the image and be funny and sarcastic about the humans in the image.
Give a short description of 100 words.""",
            },
        ]
        + script
        + generate_ChatGPT_prompt(base64_image),
        max_tokens=300,
    )
    response_text = response.choices[0].message.content
    return response_text

# capture image from webcam and if save, then save it to disk
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
        blitframe=cv2.cvtColor(np.array(pil_img), cv2.COLOR_BGR2RGB)#COLOR_BGR2RGB
        blitframe=cv2.cvtColor(blitframe, cv2.COLOR_RGB2BGR)# reencoding required for some reason.
        #convert numpy.ndarry to pygame.surface 
        blitframe=np.rot90(blitframe)
        blitframe=np.flipud(blitframe)
        blitframe = pygame.surfarray.make_surface(blitframe)
        blitframe = pygame.transform.scale(blitframe, (640,480))
        screen.blit(blitframe, (0, 0, 640, 480))

        # Save the frame as an image file
        # every 5 seconds save a frame
        if (save):
            screen.blit(blitframe, (640, 0, 640, 480))
            print("📸 Say cheese! Saving frame.")
            path = f"{folder}/frame0.jpg"
            #copy a frame on disk to save as a previous frame
            if os.path.exists(path):
                if os.path.exists(f"{folder}/frame{max_cache}.jpg"):
                    os.remove(f"{folder}/frame{max_cache}.jpg")
                for i in range(max_cache-1,-1,-1):
                    if os.path.exists(f"{folder}/frame{i}.jpg"):
                        shutil.copy(f"{folder}/frame{i}.jpg",f"{folder}/frame{i+1}.jpg")
            cv2.imwrite(path, frame)
    else:
        print("Failed to capture image")

def display_state(state_name,status,x,y):
    font = pygame.font.SysFont('Arial', 20)
    if (status):
        text_surface = font.render(state_name+" on ", True, (0, 255, 0))
    else:
        text_surface = font.render(state_name+" off", True, (255, 0, 0))
    screen.blit(text_surface, (x, y))

def display_settings(chatGPT,use_Google,elevenLabs,auto):
    display_state("(c) ChatGPT",chatGPT,1100,10)
    display_state("(g) Google",use_Google,1100,30)
    display_state("(e) ElevenLabs",elevenLabs,1100,50)
    display_state("(a) Auto",auto,1100,70)
    pygame.display.flip()    


if __name__ == "__main__":
    settings = Settings()
    settings.load()
    
    if settings.webcam is None:
        settings.webcam = select_webcam()
        settings.save()
    else:
        print(f"Loaded webcam {settings.webcam} from settings")

    client = OpenAI()

    # Initialize the webcam from settings

    cap = cv2.VideoCapture(settings.webcam) # most likely 0, but could be 1 or 2 depending on your setup
    
    # Check if the webcam is opened correctly and try 1 if fails
    if not cap.isOpened():
        cap = cv2.VideoCapture(settings.webcam+1)
        if not cap.isOpened():
            raise IOError("Cannot open webcam")
        

    set_api_key(os.environ.get("ELEVENLABS_API_KEY"))
    #define screen as global
    screen = pygame.display.set_mode((1280, 480))

    # Use `os.getenv('GOOGLE_API_KEY')` to fetch an environment variable.
    GOOGLE_API_KEY=os.getenv('GOOGLE_API_KEY')
    genai.configure(api_key=GOOGLE_API_KEY)

    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
    # set a bunch of variables
    
    use_ChatGPT = False
    use_Google = False
    ui_win = False
    talking = False
    imageTime = 3  #how long to wait to snap
    victory = False
    prevTime = time.time()
    save = False
    newshot = False
    use_ElevenLabs = False
    
    
    script = []
    pygame.init()
    pygame.mixer.init()
    pygame.font.init()  # Initialize the font module
    font = pygame.font.SysFont('Arial', 50)  # Default font, size 25
  

    

    TALKING_END = pygame.USEREVENT+1
    pygame.mixer.music.set_endevent(TALKING_END)

    screen = pygame.display.set_mode((1280, 480))
    # while not exit - talking
    
    auto = False
    running = True
    processing = not auto
    
    display_settings(use_ChatGPT,use_ElevenLabs,auto,use_Google)
    
    font = pygame.font.SysFont('Arial', 36)
    text_surface = font.render("press <space> to start countdown ", True, (255, 0, 0))  # Red text
    screen.blit(text_surface, (650, 200))
    
    
    while running:
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT:
                running = False
            #check space bar pressed
            if event.type == TALKING_END:
                print('talking end event')
                talking = False
                if (auto):
                    processing = False
                    print("autostart")
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    print("Space bar pressed")
                    processing = False
                if event.key == pygame.K_w:
                    print("win pressed")
                    ui_win = True
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r:
                    print("restart")
                    ui_win = False
                    victory = False
                if event.key == pygame.K_c:
                    print("ChatGPT now "+ str(not use_ChatGPT))
                    use_ChatGPT = not use_ChatGPT
                if event.key == pygame.K_g:
                    print("Google now "+ str(not use_Google))
                    use_Google = not use_Google
                if event.key == pygame.K_a:
                    print("auto is now "+ str(not auto))
                    auto = not auto
                    processing = not auto  # this is to simulate a space bar press
                if event.key == pygame.K_e:
                    print("elevenlabs audio"+ str(not use_ElevenLabs))
                    use_ElevenLabs = not use_ElevenLabs
                if event.key == pygame.K_s:
                    print("saving settings")
                    settings.save()
                # options to change webcam
                if event.key == pygame.K_0:
                    print("webcam 0")
                    settings.webcam = 0
                    cap.release()
                    cap = cv2.VideoCapture(0)
                    settings.save()
                if event.key == pygame.K_1:
                    print("webcam 1")
                    settings.webcam = 1
                    cap.release()
                    cap = cv2.VideoCapture(1)
                    settings.save()
                if event.key == pygame.K_2:
                    print("webcam 2")
                    settings.webcam = 2
                    cap.release()
                    cap = cv2.VideoCapture(2)
                    settings.save()
                display_settings(use_ChatGPT,use_Google,use_ElevenLabs,auto)
    
                    
                   
        # if stuff still happening reset the countdown to image timer
        if(processing):
            prevTime = time.time()
        #display countdown timer on screen
        #convert time to string
        timeString = str(imageTime-int((time.time() - prevTime)))
        # if time to take photo
        if ((time.time() - prevTime) > imageTime):
            prevTime = time.time()
            save = True 
            newshot = True 
            processing = not auto
        if (not victory):
            capture_image(save)
            if (save):
                display_settings(use_ChatGPT,use_Google,use_ElevenLabs,auto)
 
             
        save = False
        font = pygame.font.SysFont('Arial', 50)
        text_surface = font.render(timeString, True, (255, 0, 0))  # Red text
        screen.blit(text_surface, (320, 10))  # Draw text at position (50, 50)
        

         
        
        if (victory):
            font = pygame.font.SysFont('Arial', 150)
            text_surface = font.render("You Win!", True, (255, 0, 0))
            screen.blit(text_surface, (320, 50))
        
        pygame.display.flip()
        
        


       
       
        if (not talking and (use_ChatGPT or use_Google) and not victory and newshot):
            #processing = True
            
            # path to your image
            image_path = os.path.join(os.getcwd(), f"{folder}/frame0.jpg") 
            resized_image = encode_image(image_path,0.5)
            if use_ChatGPT:
                # getting the base64 encoding
                print("Sending to ChatGPT")
                analysis = custom_instructions_ChatGPT(resized_image, script=script)
                analysis = "ChatGPT says:"+analysis
            elif use_Google:
                print("Sending to Google")
                model = genai.GenerativeModel(model_name="gemini-pro-vision",
                              generation_config=generation_config(),
                              safety_settings=safety_settings())

                image_parts = [
                {
                    "mime_type": "image/jpeg",
                    "data": resized_image
                },
                ]
                prompt_parts = [
                "    Describe this image in 50 words or fewer.",
                image_parts[0],
                ]
                analysis_google = model.generate_content(prompt_parts)
                analysis = "Google says:"+analysis_google.text
            else:
                analysis = "You have not selected a service to use."

            print(analysis)
            
            font = pygame.font.SysFont('Arial', 20)
            text_surface = font.render(analysis[:50], True, (255, 0, 0))
            screen.blit(text_surface, (640, 400))
            if "[LAUGH]" in analysis:
                victory = True
            
        else:
            if ui_win:
                analysis = "This is a test [LAUGH]"
            else:
                analysis = "You have not won yet."
        
        

        
        if (not talking and newshot and not victory and use_ElevenLabs):
            newshot = False
            print("Speaking")
            talking = True
            processing = True
            play_audio(analysis,use_ElevenLabs)

        if (newshot):
            newshot = False      
        if(not talking and victory):
             laugh = pygame.mixer.Sound("assets/laugh.mp3")
             laugh.play()

        script = script + [{"role": "assistant", "content": analysis}]



cap.release()
cv2.destroyAllWindows()