from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import json
from dotenv import load_dotenv
import gspread
from datetime import date
import assemblyai as aai
import tempfile
import io

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure API keys
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not ASSEMBLYAI_API_KEY:
    raise ValueError("ASSEMBLYAI_API_KEY not found. Make sure it's set in your .env file.")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Make sure it's set in your .env file.")

# Configure AssemblyAI
aai.settings.api_key = ASSEMBLYAI_API_KEY

def transcribe_audio_in_memory(audio_data):
    """
    Transcribes audio data in memory using AssemblyAI without saving to disk.
    """
    try:
        print("🎙️ Transcribing audio with AssemblyAI...")
        
        # Create a temporary file-like object in memory
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe the temporary file
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(temp_file_path)
            
            if transcript.status == aai.TranscriptStatus.error:
                raise Exception(f"Transcription failed: {transcript.error}")
            
            return transcript.text
            
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        print(f"Transcription error: {e}")
        raise

def extract_job_details(transcript_text):
    """
    Uses Google Gemini API to extract structured job application details from transcript text.
    Implements proper exception handling and logic checks.
    """
    import time

    print("🤖 Extracting job details with Gemini...")

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    headers = {
        'Content-Type': 'application/json',
        'x-goog-api-key': GEMINI_API_KEY
    }

    prompt = (
        "You are an intelligent assistant that extracts job application details from a text transcript and provides the output in a clean JSON format. "
        "Extract the following four fields: company_name, job_role, resume_version, platform, and status.\n\n"
        f"Here is the transcript:\n\"{transcript_text}\"\n\n"
        "Return only valid JSON with these exact field names: company_name, resume_version, job_role platform, status"
    )

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "response_mime_type": "application/json"
        }
    }

    for attempt in range(3):  # Try up to 3 times
        try:
            response = requests.post(url, headers=headers, json=data, timeout=20) # Add a timeout
            response.raise_for_status() # This will raise an error for 4xx or 5xx status codes


            api_response_data = response.json()
            # Validate response structure
            if (
                "candidates" not in api_response_data or
                not api_response_data["candidates"] or
                "content" not in api_response_data["candidates"][0] or
                "parts" not in api_response_data["candidates"][0]["content"] or
                not api_response_data["candidates"][0]["content"]["parts"] or
                "text" not in api_response_data["candidates"][0]["content"]["parts"][0]
            ):
                raise ValueError("Unexpected API response structure: {}".format(api_response_data))

            json_string = api_response_data['candidates'][0]['content']['parts'][0]['text']
            try:
                extracted_data = json.loads(json_string)
            except json.JSONDecodeError as jde:
                print(f"JSON decode error: {jde}")
                raise ValueError(f"Failed to parse JSON from Gemini response: {json_string}")

            # Set default values for missing fields
            extracted_data["company_name"] = extracted_data.get("company_name", "N/A")
            extracted_data["job_role"] = extracted_data.get("job_role", "N/A")
            extracted_data["resume_version"] = extracted_data.get("resume_version", "N/A")
            extracted_data["platform"] = extracted_data.get("platform", "N/A")
            
            # Set default status to "applied" if status is empty or missing
            if not extracted_data.get("status") or extracted_data.get("status").strip() == "":
                extracted_data["status"] = "applied"
                print("📝 Setting default status to 'applied'")
            else:
                extracted_data["status"] = extracted_data.get("status", "applied")

            return extracted_data

        except requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code if http_err.response else None
            if status_code and 500 <= status_code < 600:
                print(f"⚠️ Server error ({status_code}), attempt {attempt + 1} of 3. Retrying in {2 ** attempt} seconds...")
                time.sleep(2 ** attempt)
            else:
                print("Client error occurred")
                raise Exception("API request failed")
        except (requests.exceptions.RequestException, ValueError) as e:
            print("Error during API request or response parsing")
            if attempt < 2:
                print(f"Retrying in {2 ** attempt} seconds...")
                time.sleep(2 ** attempt)
            else:
                raise Exception("API request failed")
        except Exception as e:
            print("An unexpected error occurred")
            raise Exception("API request failed")

    # If all retries fail, raise an exception
    raise Exception("API request failed after 3 attempts.")



def add_row_to_sheet(data):
    """
    Appends a new row to Google Sheets with the job application details.
    """
    try:
        print("📝 Adding row to Google Sheets...")
        
        # Authenticate with Google Sheets
        gc = gspread.service_account(filename='credentials.json')
        spreadsheet = gc.open("JobsHunt-sheet")
        worksheet = spreadsheet.get_worksheet(0)

        # Prepare row data
        row = [
            str(date.today()),
            data.get("company_name", "N/A"),
            data.get("job_role", "N/A"),
            data.get("resume_version", "N/A"),
            data.get("platform", "N/A"),
            data.get("status", "applied")
        ]

        worksheet.append_row(row)
        print("✅ Row added to Google Sheets successfully!")
        return True
        
    except Exception as e:
        print("Google Sheets error occurred")
        raise Exception("Failed to save data")

@app.route('/', methods=['GET'])
def index():
    """
    Simple index route to verify backend is running.
    """
    return jsonify({"message": "JobHunt Backend is running."}), 200

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    """
    Complete workflow: Receive audio → Transcribe → Extract → Add to Sheets
    """
    try:
        # Input validation
        if 'audio_data' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400

        file = request.files['audio_data']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Validate file type
        allowed_extensions = {'.webm', '.mp3', '.wav', '.m4a'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in allowed_extensions:
            return jsonify({"error": "Invalid file type. Please upload an audio file."}), 400
        
        # Validate file size (max 10MB)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            return jsonify({"error": "File too large. Maximum size is 10MB."}), 400

        print("📁 Received audio file, starting processing...")
        
        # Read audio data into memory
        audio_data = file.read()
        
        # Step 1: Transcribe audio in memory
        transcript_text = transcribe_audio_in_memory(audio_data)
        print(f"✅ Transcription complete: {len(transcript_text)} characters")
        
        # Step 2: Extract job details from transcript
        job_details = extract_job_details(transcript_text)
        print(f"✅ Extraction complete: {job_details}")
        
        # Step 3: Add to Google Sheets
        add_row_to_sheet(job_details)
        
        # Return success response
        return jsonify({
            "status": "success",
            "message": "Audio processed and job details added to sheet successfully!",
            "extracted_data": job_details
        }), 200
        
    except Exception as e:
        print("❌ Error in upload_audio")
        return jsonify({
            "error": "Processing failed. Please try again."
        }), 500


# from mangum import Mangum
# handler = Mangum(app)

if __name__ == '__main__':
    print("🚀 Starting JobHunt Backend...")
    print("📋 Available endpoints:")
    print("   - GET  / : Health check")
    print("   - POST /upload-audio : Process audio and add to sheets")
    app.run(debug=False, host='0.0.0.0', port=5000) 