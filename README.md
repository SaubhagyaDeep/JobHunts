# JobHunt Application Tracker 🎙️

A streamlined web application that automatically processes job application audio recordings and adds them to your Google Sheets  for effieceint tracking.

## 🚀 Streamlined Workflow

   Record audio → **Instant processing** → Added to sheets automatically!

## ✨ Key Improvements

- **⚡ Instant Processing**: No more manual file handling or script execution
- **🔄 In-Memory Operations**: Eliminates slow disk I/O operations
- **🛡️ Scalable**: Handles multiple users simultaneously without file conflicts
- **📱 Better UX**: Real-time progress feedback and extracted data display
- **🎨 Modern UI**: Beautiful, responsive interface with status indicators

## 🛠️ Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file in the project root:
```env
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Google Sheets Setup
1. Create a Google Sheet named "JobsHunt-sheet"
2. Download your service account credentials as `credentials.json`
3. Place `credentials.json` in the project root

### 4. Run the Application
```bash
python app.py
```
The server will start at `http://localhost:5000`

### 5. Open the Frontend
Open `frontend.html` in your web browser

## 📋 How It Works

1. **Record Audio**: Click "Start Recording" and speak about your job application
2. **Automatic Processing**: The system instantly:
   - Transcribes your audio using AssemblyAI
   - Extracts job details using Google Gemini
   - Adds the information to your Google Sheets
3. **View Results**: See the extracted information displayed on screen

## 🎯 Example Audio Content
Speak clearly about your job application, for example:
> "I applied to Google for a software engineer position using my resume version 2.1 on LinkedIn. The status is applied."

The system will extract:
- **Company**: Google
- **Role**: Software Engineer
- **Resume Version**: 2.1
- **Platform**: LinkedIn
- **Status**: applied

## 🚨 Troubleshooting

### Common Issues:
1. **Microphone Permission**: Ensure your browser allows microphone access
2. **API Keys**: Verify your `.env` file contains valid API keys
3. **Google Sheets**: Check that `credentials.json` is in the project root
4. **Sheet Name**: Ensure your Google Sheet is named exactly "JobsHunt-sheet"

**Happy job hunting! 🎯** 
