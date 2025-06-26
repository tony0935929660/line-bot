from setuptools import setup

APP = ['main.py']
OPTIONS = {
    'argv_emulation': True,
    'packages': ['PIL', 'pyautogui', 'pyperclip'],
    'plist': {
        'CFBundleName': 'LINE Sender',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleIdentifier': 'com.yourname.linesender',
        'NSHighResolutionCapable': True
    },
    # 👇 加這行可防止打包時自動載入無用模組
    'excludes': ['rubicon'],
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
