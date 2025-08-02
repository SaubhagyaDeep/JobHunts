import os
import json
import tempfile
from datetime import date

import boto3
import gspread
import requests
import assemblyai as aai
from flask import Flask, request, jsonify
from flask_cors import CORS
from mangum import Mangum
from asgiref.wsgi import WsgiToAsgi




# This helper function fetches secrets from AWS SSM Parameter Store
def get_secret_from_ssm(parameter_name):
    """Retrieves a secret from AWS SSM Parameter Store."""
    print(f"🤫 Fetching secret: {parameter_name}")
    try:
        ssm_client = boto3.client('ssm')
        response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
        return response['Parameter']['Value']
    except Exception as e:
        print(f"❌ Error retrieving secret {parameter_name} from SSM")
        raise Exception("Failed to retrieve configuration")


ASSEMBLYAI_API_KEY = get_secret_from_ssm(os.environ['ASSEMBLYAI_API_KEY_SSM_NAME'])
GEMINI_API_KEY = get_secret_from_ssm(os.environ['GEMINI_API_KEY_SSM_NAME'])
GCP_CREDENTIALS_JSON_STRING = get_secret_from_ssm(os.environ['GCP_CREDENTIALS_SSM_NAME'])

# Configure AssemblyAI client
aai.settings.api_key = ASSEMBLYAI_API_KEY

# MODIFICATION: Initialize Google Sheets client once during cold start
gcp_creds_dict = json.loads(GCP_CREDENTIALS_JSON_STRING)
gc = gspread.service_account_from_dict(gcp_creds_dict)
spreadsheet = gc.open("JobsHunt-sheet")


app = Flask(__name__)
CORS(app)
asgi_app = WsgiToAsgi(app)





def transcribe_audio_in_memory(audio_data):
    """Transcribes audio data using a temporary file, compatible with Lambda's /tmp directory."""
    try:
        print("🎙️ Transcribing audio with AssemblyAI...")
        # Lambda provides a writable /tmp directory
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False, dir='/tmp/') as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name

        try:
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(temp_file_path)
            if transcript.status == aai.TranscriptStatus.error:
                raise Exception("Transcription failed")
            return transcript.text
        finally:
            os.unlink(temp_file_path)
    except Exception as e:
        print("Transcription error occurred")
        raise Exception("Audio transcription failed")

def extract_job_details(transcript_text):
    
    print("🤖 Extracting job details with Gemini...")
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    headers = {'Content-Type': 'application/json', 'x-goog-api-key': GEMINI_API_KEY}
    prompt = (
        "You are an intelligent assistant that extracts job application details from a text transcript and provides the output in a clean JSON format. "
        "Extract the following fields: company_name, job_role, resume_version, platform, and status.\n\n"
        f"Here is the transcript:\n\"{transcript_text}\"\n\n"
        "Return only valid JSON with these exact field names: company_name, job_role,resume_version, platform, status"

    )
    data = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "application/json"}}

    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
        response.raise_for_status()
        api_response_data = response.json()
        json_string = api_response_data['candidates'][0]['content']['parts'][0]['text']
        extracted_data = json.loads(json_string)
        

        extracted_data["company_name"] = extracted_data.get("company_name", "N/A")
        extracted_data["job_role"] = extracted_data.get("job_role", "N/A")
        extracted_data["resume_version"] = extracted_data.get("resume_version", "N/A")
        extracted_data["platform"] = extracted_data.get("platform", "N/A")
        if not extracted_data.get("status") or extracted_data.get("status").strip() == "":
            extracted_data["status"] = "applied"
            print("📝 Setting default status to 'applied'")
        else:
            extracted_data["status"] = extracted_data.get("status", "applied")
        
        return extracted_data
    except Exception as e:
        print("Extraction error occurred")
        raise Exception("Failed to extract job details")

def add_row_to_sheet(data):
    """MODIFICATION: Appends a row using the pre-authorized Google Sheets client."""
    try:
        print("📝 Adding row to Google Sheets...")
        worksheet = spreadsheet.get_worksheet(0)
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



# @app.route('/', methods=['GET'])
# def index():
#     return jsonify({"message": "JobHunt Backend is running."})

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
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
        audio_data = file.read()
        
        transcript_text = transcribe_audio_in_memory(audio_data)
        print(f"✅ Transcription complete: {len(transcript_text)} characters")
        
        job_details = extract_job_details(transcript_text)
        print(f"✅ Extraction complete: {job_details}")
        
        add_row_to_sheet(job_details)
        
        return jsonify({
            "status": "success",
            "message": "Audio processed and job details added to sheet successfully!",
            "extracted_data": job_details
        }), 200
    except Exception as e:
        print("❌ Error in upload_audio")
        return jsonify({"error": "Processing failed. Please try again."}), 500


handler = Mangum(asgi_app)
