# main_script.py
import os
from dotenv import load_dotenv
import assemblyai as aai

# Load environment variables from the .env file
load_dotenv()

# Get the AssemblyAI API key from the environment
api_key = os.getenv("ASSEMBLYAI_API_KEY")

# Check if the API key is available
if not api_key:
    raise ValueError("ASSEMBLYAI_API_KEY not found. Make sure it's set in your .env file.")

try:
    # 1. Set the API key for the AssemblyAI SDK
    aai.settings.api_key = api_key

    # Use a .webm file instead of .mp3
    audio_file_path = "received_audio.webm"
    print("🎙️ Transcribing audio file with AssemblyAI...")

    # 2. Create a Transcriber object
    transcriber = aai.Transcriber()

    # 3. Call the transcription method
    # AssemblyAI supports webm files, but the audio must be in a supported codec (e.g., Opus or Vorbis).
    # If the file is a valid webm audio file, this should work.
    transcript = transcriber.transcribe(audio_file_path)

    # 4. Check the transcription status for errors
    if transcript.status == aai.TranscriptStatus.error:
        print(f"Transcription failed: {transcript.error}")
    else:
        # 5. Print the transcript
        print("\n📝 Transcription Complete:\n")
        print(transcript.text)
        # 6. Save the transcript to a txt file called "raw_data"
        with open("raw_data.txt", "w", encoding="utf-8") as f:
            f.write(transcript.text)
        print("✅ Transcription saved to raw_data.txt")

except FileNotFoundError:
    print(f"Error: The file '{audio_file_path}' was not found.")
except Exception as e:
    print(f"An error occurred: {e}")

# Notes:
# - This code will work with .webm files as long as the audio codec is supported by AssemblyAI (Opus or Vorbis).
# - If you get an error about unsupported format, you may need to convert the webm file to a supported format (e.g., wav or mp3).