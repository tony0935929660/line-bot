# auth_server.py
from flask import Flask, request, redirect
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

    return login(token_res.get('access_token'))

def login(accessToken):
    headers = {
        'Content-Type': 'application/json', # Or 'application/json' depending on the API's requirements
        'Accept': 'application/json'
    }

    try:
        print(accessToken)
        # 發送 POST 請求，並將資料放入 data 參數
        response = requests.post('https://www.shanlink.tech/api/AccountApi/LineTokenLogin',
            headers=headers,
            json={'accessToken': accessToken}
        )
        response.raise_for_status()
        profile_res = response.json()

        # 放入 queue 傳回 Tkinter 主程式
        login_queue.put(profile_res['user'])

        return "<h1>恭喜登入成功！請返回應用程式</h1>"

    except requests.exceptions.RequestException as e:
        print("請求失敗:", e)
        
        return redirect("https://shanlink.tech")

def start_flask_server():
    app.run(port=5000)
