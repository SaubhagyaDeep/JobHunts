# JobHunt Audio Recorder 🎙️

A streamlined web application that automatically processes job application audio recordings and adds them to your Google Sheets tracking system.

## 🚀 New Streamlined Workflow

**Before (Manual Steps):**
1. Upload audio → Save to disk
2. Manually run `text_extraction.py` → Save transcript to `raw_data.txt`
3. Manually run `data_extraction.py` → Read from `raw_data.txt` → Add to sheets

**After (Automated):**
1. Record audio → **Instant processing** → Added to sheets automatically!

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
python final.py
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
- **Resume Version**: 2.1
- **Platform**: LinkedIn
- **Status**: applied

## 📁 Project Structure

```
JobHunts/
├── final.py              # 🆕 Unified backend (use this!)
├── frontend.html         # 🆕 Updated frontend with better UX
├── requirements.txt      # 🆕 Dependencies
├── README.md            # 🆕 This file
├── .env                 # Environment variables
├── credentials.json     # Google Sheets credentials
├── app.py               # Old backend (deprecated)
├── text_extraction.py   # Old transcription script (deprecated)
├── data_extraction.py   # Old extraction script (deprecated)
└── raw_data.txt         # Old output file (no longer needed)
```

## 🔧 API Endpoints

- `GET /` - Health check
- `POST /upload-audio` - Process audio and add to sheets

## 🚨 Troubleshooting

### Common Issues:

1. **Microphone Permission**: Ensure your browser allows microphone access
2. **API Keys**: Verify your `.env` file contains valid API keys
3. **Google Sheets**: Check that `credentials.json` is in the project root
4. **Sheet Name**: Ensure your Google Sheet is named exactly "JobsHunt-sheet"

### Error Messages:
- "ASSEMBLYAI_API_KEY not found" → Check your `.env` file
- "GEMINI_API_KEY not found" → Check your `.env` file
- "Google Sheets error" → Verify `credentials.json` and sheet name

## 🎉 Benefits of the New System

- **Time Savings**: No more manual script execution
- **Reliability**: Eliminates file corruption risks
- **Scalability**: Handles multiple concurrent users
- **User Experience**: Real-time feedback and progress indicators
- **Maintenance**: Single codebase to maintain

## 🔄 Migration from Old System

If you were using the old system:
1. Stop using `app.py`, `text_extraction.py`, and `data_extraction.py`
2. Use `final.py` instead
3. The frontend will work with the new backend automatically
4. No more need to manually run scripts or check `raw_data.txt`

---

**Happy job hunting! 🎯** 