from flask import Flask, request, render_template, send_file
import os
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from googletrans import Translator
from transformers import pipeline
from fpdf import FPDF

app = Flask(__name__)
translator = Translator()
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

def extract_text(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    if not text:
        images = convert_from_path(file_path)
        for img in images:
            text += pytesseract.image_to_string(img, lang='hin+eng')
    return text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    pdf = request.files['pdf_file']
    filename = os.path.join("temp", pdf.filename)
    pdf.save(filename)

    hindi_text = extract_text(filename)
    english_text = translator.translate(hindi_text, src='hi', dest='en').text
    summary_hi = summarizer(hindi_text[:1000])[0]['summary_text']
    summary_en = summarizer(english_text[:1000])[0]['summary_text']

    return render_template("result.html", hindi=hindi_text, english=english_text,
                           summary_hi=summary_hi, summary_en=summary_en)

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    text = request.form['text']
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text)
    output_path = "temp/translated_output.pdf"
    pdf.output(output_path)
    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)