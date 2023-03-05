import pyaudio
import speech_recognition as sr

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

r = sr.Recognizer()

p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

while True:
    data = stream.read(CHUNK)
    try:
        text = r.recognize_google(data, language='en-US')
        if text == 'Hello':
            print('Hello!')
    except sr.UnknownValueError:
        pass
