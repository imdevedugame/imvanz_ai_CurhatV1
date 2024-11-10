import requests
import speech_recognition as sr
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')


# Variabel global untuk menyimpan nama panggilan dan topik
nickname = ""
topic = ""

# Fungsi untuk mendapatkan respons dari AI
def get_ai_response(prompt):
    global nickname  # Pastikan menggunakan nickname terbaru
    prompt_with_instruction = f"{prompt}. Jawablah dalam bahasa Indonesia, dan panggil aku {nickname}."
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": "Bearer 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",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta/llama3-70b-instruct",
        "messages": [{"role": "user", "content": prompt_with_instruction}],
        "temperature": 0.5,
        "top_p": 1,
        "max_tokens": 1024,
        "stream": False
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code}"

# Fungsi untuk menangkap suara pengguna
def listen_and_recognize():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Silakan bicara...")
        audio = recognizer.listen(source)

    try:
        print("Sedang mengenali...")
        text = recognizer.recognize_google(audio, language="id-ID")
        print(f"Anda: {text}")
        return text
    except sr.UnknownValueError:
        print("Tidak dapat mengenali ucapan.")
        return None
    except sr.RequestError:
        print("Kesalahan dalam permintaan ke Google API.")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('initialize_chat')
def initialize_chat(data):
    global nickname, topic
    nickname = data.get('nickname', '')  # Gunakan `get` untuk keamanan
    topic = data.get('topic', '')  # Gunakan `get` untuk keamanan
    welcome_message = f"Hai {nickname}, siap ngobrol tentang {topic}!"
    emit('ai_response', welcome_message)

@socketio.on('get_ai_response')
def handle_voice_input():
    user_input = listen_and_recognize()
    if user_input:
        response = get_ai_response(user_input)
        emit('ai_response', response)

@socketio.on('user_message')
def handle_text_input(data):
    # Memastikan bahwa data adalah dictionary
    if isinstance(data, dict):
        user_input = data.get('message', '')
    else:
        user_input = data  # Jika data adalah string, langsung gunakan

    if user_input:
        response = get_ai_response(user_input)
        emit('ai_response', response)

if __name__ == "__main__":
    socketio.run(app, debug=True)
