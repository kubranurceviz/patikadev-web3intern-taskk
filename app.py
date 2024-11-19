from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import fitz
from github_api import GitHubClient
from fpdf import FPDF
import openai

import requests

MOTOKO_API_URL = "https://m7sm4-2iaaa-aaaab-qabra-cai.raw.ic0.app/?tag=2418358693"

# Yetenek ekleme fonksiyonu
def add_skill_to_motoko(user_id, skill):
    try:
        response = requests.get(f"{MOTOKO_API_URL}/addSkill/{user_id}/{skill}")
        response.raise_for_status()  # HTTP hatası varsa istisna fırlatır
        data = response.json()  # JSON yanıtını al
        return data.get('message', 'Yetenek başarıyla eklendi.')  # JSON'dan bir mesaj al
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"  # Hata mesajını döndür

# Yetenek onaylama fonksiyonu
def approve_skill_in_motoko(user_id, skill):
    try:
        response = requests.get(f"{MOTOKO_API_URL}/approveSkill/{user_id}/{skill}")
        response.raise_for_status()  # HTTP hatası varsa istisna fırlatır
        data = response.json()  # JSON yanıtını al
        return data.get('message', 'Yetenek başarıyla onaylandı.')  # JSON'dan bir mesaj al
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"  # Hata mesajını döndür

# Kullanıcının yeteneklerini getirme fonksiyonu
def get_user_skills_from_motoko(user_id):
    try:
        response = requests.get(f"{MOTOKO_API_URL}/getUserSkills/{user_id}")
        response.raise_for_status()  # HTTP hatası varsa istisna fırlatır
        data = response.json()  # JSON yanıtını al
        return data.get('skills', [])  # JSON'dan 'skills' verisini al
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"  # Hata mesajını döndür


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.secret_key = os.urandom(24)

#openai anahtarınızı eklemeniz lazım github kabul etmediğinden satırı kaldırak zorundayım

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as pdf:
        for page_num in range(pdf.page_count):
            page = pdf[page_num]
            text += page.get_text()
    return text

def analyze_skills(cv_text, github_data_text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[ 
                {"role": "system", "content": "Bir insan kaynakları uzmanı olarak hareket et."},
                {"role": "user", "content": f"CV içeriği:\n{cv_text}\nGitHub verileri:\n{github_data_text}\nBu kişinin hangi teknolojilerde uzman olduğunu analiz et ve onayla."}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error during OpenAI API call: {e}")
        return "Hata oluştu, lütfen tekrar deneyin."

def generate_pdf_report(username, skills_analysis):
    pdf = FPDF()
    pdf.add_page()

    # Font dosyasının doğru yolu
    font_path = os.path.join(os.getcwd(), 'dejavu-sans', 'DejaVuSans.ttf')  # Font dosyasının doğru yolu
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Font dosyası bulunamadı: {font_path}")
    
    pdf.add_font('DejaVu', '', font_path, uni=True)
    pdf.set_font('DejaVu', '', 12)  # Unicode fontu kullan

    pdf.cell(200, 10, txt=f"{username} için Yetenek Raporu", ln=True, align='C')
    pdf.ln(10)

    # Skill analizi metnini PDF'e yazıyoruz
    pdf.multi_cell(0, 10, txt=skills_analysis)

    # PDF dosyasını kaydetme yolu
    pdf_file = os.path.join('uploads', f"{username}_skills_report.pdf")
    pdf.output(pdf_file)

    return pdf_file

# Flask Routes
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        github_username = request.form['github_username']
        session['github_username'] = github_username
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        cv_file = request.files['cv']
        if not cv_file.filename.endswith('.pdf'):
            return "Sadece PDF dosyaları yüklenebilir", 400

        cv_filename = os.path.join(app.config['UPLOAD_FOLDER'], cv_file.filename)
        cv_file.save(cv_filename)
        cv_text = extract_text_from_pdf(cv_filename)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (username, password, github_username, cv_text) VALUES (?, ?, ?, ?)',
            (username, hashed_password, github_username, cv_text)
        )
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['github_username'] = user['github_username']
            return redirect(url_for('dashboard'))
        else:
            return "Yanlış kullanıcı adı veya şifre"

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('dashboard.html', username=session['username'])

@app.route('/fetch_github_data', methods=['POST'])
def fetch_github_data():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    github_token = request.form['github_token']
    github_username = session.get('github_username')

    if github_username and github_token:
        github_client = GitHubClient(github_token)
        repositories = github_client.get_repositories(github_username)

        conn = get_db()
        cursor = conn.cursor()

        github_data_text = ""
        for repo in repositories:
            github_data_text += f"Repo: {repo['name']}\n"
            for commit in repo['commits']:
                github_data_text += f"Commit: {commit['message']}\n"

        cursor.execute('SELECT cv_text FROM users WHERE id = ?', (session['user_id'],))
        cv_text = cursor.fetchone()['cv_text']

        skills_analysis = analyze_skills(cv_text, github_data_text)
        pdf_path = generate_pdf_report(session['username'], skills_analysis)

        # Add skill to Motoko
        add_skill_to_motoko(session['user_id'], skills_analysis)

        return redirect(f"/download/{os.path.basename(pdf_path)}")

    return redirect(url_for('dashboard'))

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)