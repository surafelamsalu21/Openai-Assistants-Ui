import chardet
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import openai
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import pdfplumber
# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key")

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Define a sample password (can be stored in .env file)
PASSWORD = os.getenv("LOGIN_PASSWORD", "your_password")

# Existing assistant IDs
BOOK_WRITER_ASSISTANT_ID = os.getenv("BOOK_WRITER_ASSISTANT_ID")
VANILLA_ASSISTANT_ID = os.getenv("VANILLA_ASSISTANT_ID")
CHOKO_ASSISTANT_ID = os.getenv("CHOKO_ASSISTANT_ID")
LANGCHAIN_ASSISTANT_ID = os.getenv("LANGCHAIN_ASSISTANT_ID")

# New specialized assistant IDs
MEETING_SUMMARY_ASSISTANT_ID = os.getenv("MEETING_SUMMARY_ASSISTANT_ID")
PROJECT_CREATION_ASSISTANT_ID = os.getenv("PROJECT_CREATION_ASSISTANT_ID")
ASSIGNMENT_CREATION_ASSISTANT_ID = os.getenv("ASSIGNMENT_CREATION_ASSISTANT_ID")

# Placeholder assistant IDs for testing
ASSISTANT_1_ID = os.getenv("ASSISTANT_1_ID")
ASSISTANT_2_ID = os.getenv("ASSISTANT_2_ID")
ASSISTANT_3_ID = os.getenv("ASSISTANT_3_ID")
ASSISTANT_4_ID = os.getenv("ASSISTANT_4_ID")
ASSISTANT_5_ID = os.getenv("ASSISTANT_5_ID")

# Define placeholder responses for testing
ASSISTANT_RESPONSES = {
    ASSISTANT_1_ID: "Hello",
    ASSISTANT_2_ID: "Chocolate",
    ASSISTANT_3_ID: "Banana",
    ASSISTANT_4_ID: "Strawberry",
    ASSISTANT_5_ID: "Vanilla"
}

# Allowed audio extensions
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a'}

# Check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Define the system prompt for post-processing
system_prompt = "You are a helpful assistant for the company ZyntriQix. Your task is to correct spelling discrepancies..."

# Define the function for generating a corrected transcript
def generate_corrected_transcript(temperature, system_prompt, audio_text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": audio_text}
        ]
    )
    return response['choices'][0]['message']['content']

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid password")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template(
        'landing.html',
        MEETING_SUMMARY_ASSISTANT_ID=MEETING_SUMMARY_ASSISTANT_ID,
        PROJECT_CREATION_ASSISTANT_ID=PROJECT_CREATION_ASSISTANT_ID,
        ASSIGNMENT_CREATION_ASSISTANT_ID=ASSIGNMENT_CREATION_ASSISTANT_ID,
        LANGCHAIN_ASSISTANT_ID=LANGCHAIN_ASSISTANT_ID,
        BOOK_WRITER_ASSISTANT_ID=BOOK_WRITER_ASSISTANT_ID,
        VANILLA_ASSISTANT_ID=VANILLA_ASSISTANT_ID,
        CHOKO_ASSISTANT_ID=CHOKO_ASSISTANT_ID,
        ASSISTANT_1_ID=ASSISTANT_1_ID,
        ASSISTANT_2_ID=ASSISTANT_2_ID,
        ASSISTANT_3_ID=ASSISTANT_3_ID,
        ASSISTANT_4_ID=ASSISTANT_4_ID,
        ASSISTANT_5_ID=ASSISTANT_5_ID
    )

@app.route('/chat')
def chat():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    assistant_id = request.args.get('assistant_id')
    if not assistant_id:
        return redirect(url_for('index'))
    return render_template('index.html', assistant_id=assistant_id)

@app.route('/create_thread', methods=['GET'])
def create_thread():
    try:
        thread = openai.beta.threads.create()
        return jsonify({"thread_id": thread.id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask_openai():
    data = request.json
    thread_id = data.get('thread_id')
    user_input = data.get('input')
    assistant_id = data.get('assistant_id')

    if not user_input:
        return jsonify({"error": "No input provided"}), 400
    if not thread_id:
        return jsonify({"error": "No thread provided"}), 400
    if not assistant_id:
        return jsonify({"error": "No assistant ID provided"}), 400

    if assistant_id in ASSISTANT_RESPONSES:
        return jsonify({"response": ASSISTANT_RESPONSES[assistant_id]})

    try:
        message = openai.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_input
        )

        run = openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )

        while True:
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            if run_status.status == 'completed':
                break

        messages = openai.beta.threads.messages.list(thread_id=thread_id)

        for message in messages.data:
            if message.role == "assistant":
                return jsonify({"response": message.content[0].text.value})

        return jsonify({"error": "No response from assistant"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# New route to handle audio transcription and correction
@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join('/tmp', filename)
        file.save(file_path)

        # Transcribe using Whisper
        transcript_response = openai.Audio.transcribe("whisper-1", open(file_path, "rb"))
        audio_text = transcript_response['text']

        # Send to GPT-4 for post-processing
        corrected_text = generate_corrected_transcript(0, system_prompt, audio_text)

        return jsonify({"transcript": corrected_text})
    else:
        return jsonify({"error": "Invalid file type"}), 400
from flask import request, jsonify
import pdfplumber
import openai

# Initialize OpenAI API client

@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file and file.filename.lower().endswith('.pdf'):
        try:
            # Extract text from PDF
            content = ""
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    content += page.extract_text() or ""

            if not content.strip():
                return jsonify({"error": "No text could be extracted from the PDF."}), 400

            # Generate corrected transcript using OpenAI
            temperature = 0.7
            system_prompt = "Correct the following text to improve readability and grammar."
            
            # Use the new API call syntax
            completion = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": content}],
                temperature=temperature
            )

            return jsonify({"response": completion.choices[0].message.content})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid file type. Only PDF files are supported."}), 400

if __name__ == '__main__':
    if os.getenv("FLASK_ENV") == "development":
        app.run(debug=True, host='0.0.0.0', port=5000)
