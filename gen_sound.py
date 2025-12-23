from gtts import gTTS
import os

text = "مرحباً بك في السيرفر، نتمنى لك وقتاً ممتعاً!"
language = 'ar'

if not os.path.exists("welcome.mp3"):
    try:
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save("welcome.mp3")
        print("welcome.mp3 created successfully.")
    except Exception as e:
        print(f"Error creating audio: {e}")
else:
    print("welcome.mp3 already exists.")
