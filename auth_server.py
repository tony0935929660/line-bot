# auth_server.py
from flask import Flask, request, redirect
import requests, os
from dotenv import load_dotenv
from queue import Queue
import shared

load_dotenv()

app = Flask(__name__)
login_queue = Queue()  # 共享給主程式使用

# 從環境變數取得敏感資訊
LINE_CLIENT_ID = os.getenv('LINE_CLIENT_ID')
LINE_CLIENT_SECRET = os.getenv('LINE_CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
SHANLINK_API_BASE_URL = os.getenv('SHANLINK_API_BASE_URL')
LOGIN_API_ENDPOINT = os.getenv('LOGIN_API_ENDPOINT')
SUCCESS_REDIRECT_URL = os.getenv('SUCCESS_REDIRECT_URL')
FAIL_REDIRECT_URL = os.getenv('FAIL_REDIRECT_URL')
AUTH_SERVER_PORT = int(os.getenv('AUTH_SERVER_PORT', 5123))

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
        api_url = f"{SHANLINK_API_BASE_URL}{LOGIN_API_ENDPOINT}"
        response = requests.post(api_url,
            headers=headers,
            json={'accessToken': accessToken}
        )
        response.raise_for_status()
        profile_res = response.json()
        print("登入成功:", profile_res)

        # 放入 queue 傳回 Tkinter 主程式
        login_queue.put({
            "user": profile_res['user'],
            "token": profile_res.get('token')
        })

        return redirect(SUCCESS_REDIRECT_URL)

    except requests.exceptions.RequestException as e:
        print("請求失敗:", e)
        
        return redirect(FAIL_REDIRECT_URL)

def start_flask_server():
    app.run(port=AUTH_SERVER_PORT)
