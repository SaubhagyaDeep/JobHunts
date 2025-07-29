import os
import requests
import json
from dotenv import load_dotenv
import gspread
from datetime import date

# Load environment variables from the .env file
load_dotenv()

def extract_job_details(transcript_text):
    """
    Uses the Google AI API to extract structured job application details
    from a raw text transcript.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file.")

    # 1. Define the API endpoint and headers
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    headers = {
        'Content-Type': 'application/json',
        'x-goog-api-key': api_key
    }

    # 2. Construct the prompt using the specified format
    prompt = f"""You are an intelligent assistant that extracts job application details from a text transcript and provides the output in a clean JSON format. Append the date of the application yourself. Extract the following four fields: company_name, resume_version, platform, and status.
    
    Here is the transcript:
    "{transcript_text}"
    """

    # 3. Create the JSON payload for the API request
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
        # Enforce JSON output
        "generationConfig": {
            "response_mime_type": "application/json"
        }
    }

    print("🤖 Sending transcript to Gemini for extraction...")
    
    # 4. Make the POST request to the API
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        # 5. Parse the JSON response from the API
        api_response_data = response.json()
        
        # 6. Extract the text containing the JSON data
        # The actual data is nested inside the response object
        json_string = api_response_data['candidates'][0]['content']['parts'][0]['text']
        
        # 7. Convert the JSON string into a Python dictionary
        extracted_data = json.loads(json_string)
        
        return extracted_data

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response content: {response.text}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def add_row_to_sheet(data):
    """
    Appends a new row to a Google Sheet with the job application details.
    """
    try:
        print("📝 Connecting to Google Sheets...")
        # Authenticate using the downloaded credentials file
        gc = gspread.service_account(filename='credentials.json')

        # Open the spreadsheet by its title
        # Make sure this matches the exact title of your Google Sheet
        spreadsheet = gc.open("JobsHunt-sheet") 

        # Select the first worksheet
        worksheet = spreadsheet.get_worksheet(0)

        # Prepare the row data in the correct order for your columns
        # Example Column Order: Date, Company, Resume, Platform, Status
        row = [
            str(date.today()),
            data.get("company_name", ""),
            data.get("resume_version", ""),
            data.get("platform", ""),
            data.get("status", "applied")
        ]

        worksheet.append_row(row)
        print("✅ Row added to Google Sheets successfully!")
        return True
    except Exception as e:
        print(f"Error adding row to Google Sheets: {e}")
        return False


# --- Example Usage ---
if __name__ == "__main__":
    # Read the transcript from raw_data.txt
    try:
        with open("raw_data.txt", "r", encoding="utf-8") as f:
            transcript_text = f.read().strip()
    except FileNotFoundError:
        print("raw_data.txt not found. Please ensure the file exists.")
        exit(1)

       # 1. Extract details from the transcript
    job_details = extract_job_details(transcript_text)

    # 2. If extraction is successful, add the details to the sheet
    if job_details:
        print("\n✅ Successfully extracted details:\n")
        print(json.dumps(job_details, indent=2))

        add_row_to_sheet(job_details)