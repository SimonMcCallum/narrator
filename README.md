# Make Me Laugh 

A development of the naration app to be about making ChatGPT 4 laugh after reading a description of an image

## Setup

Make sure us have 
* a recent install of python eg [Python 3.12](https://www.python.org/downloads/release/python-3121/) (make sure the System environment variable "path" is updated to include the install.
* an [OpenAI](https://platform.openai.com) API account, and create a token for API access.  This will require a payment and each image processed will require payment
* an [ElevenLabs](https://elevenlabs.io) account, and a voice ID that you plan to use to read out the image


Clone this repo, and setup and activate a virtualenv (for windows using powershell this is):

```bash
python -m pip install virtualenv
python -m virtualenv venv
.\venv\Scripts\activate.bat
```

Then, install the dependencies:
`pip install -r requirements.txt`

set your system envrionment variables to the tokens from OpenAI and Elevenlabs (set them permanently in the system or use these temporary settings):

```
$Env:OPENAI_API_KEY="<token>"
$Env:ELEVENLABS_API_KEY="<eleven-token>"
```

Make a new voice in Eleven and get the voice id of that voice using their [get voices](https://elevenlabs.io/docs/api-reference/voices) API, or by clicking the flask icon next to the voice in the VoiceLab tab.

```
$Env:ELEVENLABS_VOICE_ID="<voice-id>"
```

## Run it!

In on terminal, run the webcam capture:
```bash
python capture.py
```

The system starts in debug mode, you need to press "n" to make it connect to the internet for processing and "e" for it to send text to elevenlabs

## Keys
The keyboard controls are
* c : toggle on and off connecting to internet services including ChatGPT
* e : toggle on and off using elevenlabs to generate the audio
* <space> : start 3 second countdown to taking a photo
* a : turn on auto capture mode where it takes another photo automatically 3 seconds after the previous photo was processed.
* r : reset the system after making it laugh
* w : artificially make the system laugh


