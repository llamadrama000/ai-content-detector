from flask import Flask, request, render_template, jsonify
import os
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from docx import Document
from transformers import pipeline
from pyngrok import ngrok  # For public URL

app = Flask(__name__, template_folder='.', static_folder='.')
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load AI detection model
detector = pipeline("text-classification", model="openai-community/roberta-large-openai-detector", truncation=True, max_length=512)

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(file_path: str) -> str:
    ext = file_path.rsplit('.', 1)[1].lower()
    try:
        if ext == 'txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif ext == 'pdf':
            reader = PdfReader(file_path)
            text = ''
            for page in reader.pages:
                text += page.extract_text() or ''
            return text
        elif ext == 'docx':
            doc = Document(file_path)
            text = ''
            for para in doc.paragraphs:
                text += para.text + '\n'
            return text
        return ''
    except Exception:
        return ''

def analyze_text(text: str) -> dict:
    chunks = [text[i:i + 500] for i in range(0, len(text), 500)]
    ai_score = 0
    total_chunks = len(chunks)
    
    for chunk in chunks:
        result = detector(chunk)[0]
        ai_score += result['score'] if result['label'] == 'POSITIVE' else (1 - result['score'])
    
    ai_percentage = (ai_score / total_chunks) * 100 if total_chunks > 0 else 0
    student_percentage = 100 - ai_percentage
    confidence = min(ai_score / total_chunks, 0.99) if total_chunks > 0 else 0.95
    
    return {
        'ai_percentage': round(ai_percentage, 2),
        'student_percentage': round(student_percentage, 2),
        'confidence': round(confidence, 2)
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text_input = request.form.get('text_input')
        file = request.files.get('file_input')

        if text_input:
            result = analyze_text(text_input)
        elif file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            text = extract_text_from_file(file_path)
            if text:
                result = analyze_text(text)
            else:
                return jsonify({'error': 'Could not extract text from file.'}), 400
            os.remove(file_path)
        else:
            return jsonify({'error': 'Invalid input. Provide text or a valid file (TXT, PDF, DOCX).'}), 400

        return render_template('index.html', result=result)
    return render_template('index.html', result=None)

if __name__ == '__main__':
    # Start Flask on port 5000
    port = 5000
    # Open an ngrok tunnel to make it public
    public_url = ngrok.connect(port).public_url
    print(f"Public URL: {public_url}")
    # Run the app
    app.run(host='0.0.0.0', port=port)
