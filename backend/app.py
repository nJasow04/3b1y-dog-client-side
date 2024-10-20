import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from google.cloud import texttospeech
from groq import Groq
import uuid

# Load environment variables from .env file
load_dotenv()

# Set Google Application Credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'gcp-yt.json'

# Initialize Google Text-to-Speech client
tts_client = texttospeech.TextToSpeechClient()

# Initialize Groq client
client = Groq(
    # This is the default and can be omitted
    api_key=os.environ.get("GROQ_API_KEY"),
)

app = Flask(__name__)

# Ensure the 'static' directory exists for serving audio files
os.makedirs('static', exist_ok=True)

@app.route("/audio-input", methods=["POST"])
def audio_input():
    # Check if the request contains an audio file
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file in request'}), 400

    audio_file = request.files['audio']
    selected_language = request.form.get('language', 'en')  # Default to English US if not provided

    print("Selected language:", selected_language)

    # Save the uploaded audio file with a unique filename
    original_filename = audio_file.filename
    if original_filename == '':
        original_filename = 'uploaded_audio'
    else:
        original_filename = os.path.splitext(original_filename)[0]
    uploaded_extension = os.path.splitext(audio_file.filename)[1] or '.webm'
    uploaded_filename = f"{original_filename}{uploaded_extension}"
    uploaded_path = os.path.join('static', uploaded_filename)
    audio_file.save(uploaded_path)

    # Send the audio file directly to the Whisper API for transcription
    try:
        # Send the audio file to Whisper API
        transcript_response = client.audio.transcriptions.create(
            model="whisper-large-v3", 
            language=None,
            file=Path(uploaded_path),
            response_format="json"
        )
        transcript = transcript_response.text
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return jsonify({'error': 'Failed to transcribe audio'}), 500

    # Translate the transcription into the selected language using GPT model via Groq
    try:
        # Use the Chat Completion API for better translation
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a helpful assistant that translates text to {selected_language}. \
Please provide the translation without any additional text."
                },
                {
                    "role": "user",
                    "content": transcript
                }
            ],
            temperature=0.5,
        )
        translated_text = completion.choices[0].message.content.strip()
        print("Translated Text:", translated_text)
    except Exception as e:
        print(f"Error translating text: {e}")
        return jsonify({'error': 'Failed to translate text'}), 500

    # Convert the translated text to speech using Google TTS
    try:
        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=translated_text)

        # Build the voice request, select the language code and the ssml voice gender
        voice = texttospeech.VoiceSelectionParams(
            language_code=selected_language,
            # Select a voice based on language; you can customize this as needed
            # For example, using the first available voice for the language
            name=select_voice(selected_language)
        )

        # Select the type of audio file you want returned
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        # Perform the text-to-speech request on the translated text
        response = tts_client.synthesize_speech(
            input=synthesis_input, 
            voice=voice, 
            audio_config=audio_config
        )

        # Generate a unique filename for the synthesized audio
        audio_filename = f"{uuid.uuid4()}.mp3"
        audio_output_path = os.path.join('static', audio_filename)

        # Write the response to the output file
        with open(audio_output_path, 'wb') as out:
            out.write(response.audio_content)
            print(f'Audio content written to file {audio_output_path}')

    except Exception as e:
        print(f"Error in text-to-speech synthesis: {e}")
        return jsonify({'error': 'Failed to synthesize speech'}), 500

    # Return the translated text and the URL to the synthesized audio
    return jsonify({
        'message': 'Audio file received, transcribed, translated, and synthesized successfully',
        'transcript': transcript,
        'translated_text': translated_text,
        'language': selected_language,
        'audio_url': f"/static/{audio_filename}"
    }), 200

def select_voice(language_code):
    """
    Selects an appropriate voice based on the chosen language.
    You can expand this mapping as needed.
    """
    voice_mapping = {
        'en': 'en-US-Wavenet-D',
        'es': 'es-ES-Wavenet-D',
        'fr': 'fr-FR-Wavenet-D',
        'de': 'de-DE-Wavenet-D',
        'it': 'it-IT-Wavenet-D',
        # Add more mappings as needed
    }

    return voice_mapping.get(language_code, 'en-US-Wavenet-D')  # Default to English US if not found

# Route to serve static audio files
@app.route('/static/<path:filename>')
def serve_audio(filename):
    return send_from_directory('static', filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
