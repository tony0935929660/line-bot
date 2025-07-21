# auth_server.py
from flask import Flask, request
import requests, os
from dotenv import load_dotenv
from queue import Queue
import shared

load_dotenv()

app = Flask(__name__)
login_queue = Queue()  # 共享給主程式使用

LINE_CLIENT_ID = os.getenv("LINE_CHANNEL_ID")
LINE_CLIENT_SECRET = os.getenv("LINE_CHANNEL_SECRET")
REDIRECT_URI = os.getenv("LINE_REDIRECT_URI")

@app.route('/callback')
def callback():
    code = request.args.get('code')
    received_state = request.args.get('state')
    if received_state != shared.state:
        return "CSRF detected!", 400

    # 交換 token
    token_res = requests.post(
        'https://api.line.me/oauth2/v2.1/token',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'client_id': LINE_CLIENT_ID,
            'client_secret': LINE_CLIENT_SECRET,
        }
    ).json()

    access_token = token_res.get('access_token')
    profile_res = requests.get(
        'https://api.line.me/v2/profile',
        headers={'Authorization': f'Bearer {access_token}'}
    ).json()

    # 放入 queue 傳回 Tkinter 主程式
    login_queue.put(profile_res)

    return "<h1>恭喜登入成功！請返回應用程式</h1>"

def start_flask_server():
    app.run(port=5000)
