from flask import Flask, request, render_template, jsonify
import os
from werkzeug.utils import secure_filename
import random  # Placeholder for AI detection
from PyPDF2 import PdfReader
from docx import Document

app = Flask(__name__, template_folder='.', static_folder='.')
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(file_path: str) -> str:
    ext = file_path.rsplit('.', 1)[1].lower()
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

def analyze_text(text: str) -> dict:
    # Placeholder for AI detection logic
    # Replace with a real model (e.g., HuggingFace transformers) for accuracy
    ai_percentage = random.uniform(0, 100)
    student_percentage = 100 - ai_percentage
    confidence = random.uniform(0.7, 0.99)
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
            os.remove(file_path)  # Clean up
        else:
            return jsonify({'error': 'Invalid input. Provide text or a valid file (TXT, PDF, DOCX).'}), 400

        return render_template('index.html', result=result)
    return render_template('index.html', result=None)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
