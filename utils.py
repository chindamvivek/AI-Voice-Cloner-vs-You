import azure.cognitiveservices.speech as speechsdk
from config import SPEECH_KEY, SPEECH_REGION
import sounddevice as sd
from scipy.io.wavfile import write
import json
from pathlib import Path

# 1. Transcribe
def record_to_text(audio_path):
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    audio_config = speechsdk.AudioConfig(filename=audio_path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    result = recognizer.recognize_once()
    return result.text if result.reason == speechsdk.ResultReason.RecognizedSpeech else ""

# 2. Synthesize with error handling
def synthesize_text(text, output_path, voice="en-US-JennyNeural"):
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
    speech_config.speech_synthesis_voice_name = voice
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    try:
        result = synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("[INFO] Speech synthesized and saved.")
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            print(f"[ERROR] Speech synthesis canceled: {cancellation.reason}")
            if cancellation.reason == speechsdk.CancellationReason.Error:
                print(f"[ERROR] Error details: {cancellation.error_details}")
            raise RuntimeError("Speech synthesis failed. See logs.")
    except Exception as e:
        print(f"[EXCEPTION] TTS error: {e}")
        raise RuntimeError("❌ Could not synthesize the text. Please try again.")

# 3. Record from Mic
def record_from_mic(filename="temp_audio/real.wav", duration=5, fs=44100):
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    write(filename, fs, recording)
    return filename

# 4. Leaderboard
LEADERBOARD_FILE = "leaderboard.json"

def save_score(name, correct, total):
    Path(LEADERBOARD_FILE).touch(exist_ok=True)
    data = []

    try:
        with open(LEADERBOARD_FILE, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        pass

    data.append({
        "name": name,
        "correct": correct,
        "total": total
    })

    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_leaderboard():
    try:
        with open(LEADERBOARD_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def clear_leaderboard():
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump([], f)
