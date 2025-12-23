from gtts import gTTS
import os

prayers = {
    "fajr": "حان الآن موعد أذان الفجر",
    "dhuhr": "حان الآن موعد أذان الظهر",
    "asr": "حان الآن موعد أذان العصر",
    "maghrib": "حان الآن موعد أذان المغرب",
    "isha": "حان الآن موعد أذان العشاء"
}

for prayer, text in prayers.items():
    filename = f"{prayer}.mp3"
    if not os.path.exists(filename):
        try:
            print(f"Generating {filename}...")
            tts = gTTS(text=text, lang='ar', slow=False)
            tts.save(filename)
            print(f"Created {filename}")
        except Exception as e:
            print(f"Error creating {filename}: {e}")
    else:
        print(f"{filename} already exists.")
