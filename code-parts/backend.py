from flask import Flask, request, jsonify
from flask_cors import CORS

# Initialize the Flask application
app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def index():
    """
    Simple index route to verify backend is running.
    """
    return jsonify({"message": "Backend is running."}), 200

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    """
    Receives an audio file and saves it to the disk.
    """
    # Check if the 'audio_data' file is in the request
    if 'audio_data' not in request.files:
        return jsonify({"error": "No audio file part"}), 400

    file = request.files['audio_data']

    # Check if a file was selected
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Save the file to disk
    try:
        file.save('received_audio.webm')
        print("File saved successfully: received_audio.webm")
        # Return a success response
        return jsonify({
            "status": "success",
            "message": "File uploaded and saved successfully."
        }), 200
    except Exception as e:
        print(f"Error saving file: {e}")
        return jsonify({"error": f"Failed to save file: {e}"}), 500

if __name__ == '__main__':
    # Run the app on host 0.0.0.0 to make it accessible
    # from your local network.
    app.run(debug=True, host='0.0.0.0', port=5000)