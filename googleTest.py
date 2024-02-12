from pathlib import Path
import google.generativeai as genai
import os
from googlegen import generation_config, safety_settings

GOOGLE_API_KEY=os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)



model = genai.GenerativeModel(model_name="gemini-pro-vision",
                              generation_config=generation_config(),
                              safety_settings=safety_settings())

folder = "frames"
frames_dir = os.path.join(os.getcwd(), folder)
os.makedirs(frames_dir, exist_ok=True)
path = f"{folder}/frame0.jpg"

# Validate that an image is present
if not (img := Path(path)).exists():
  raise FileNotFoundError(f"Could not find image: {img}")

image_parts = [
  {
    "mime_type": "image/jpeg",
    "data": Path(path).read_bytes()
  },
]

prompt_parts = [
  "explain the associated image",
  image_parts[0],
]

response = model.generate_content(prompt_parts)
print(response.text)