from setuptools import setup

APP = ['main.py']
OPTIONS = {
    'argv_emulation': False,
    'packages': [
        'pyautogui',
        'pyperclip',
        'PIL',
    ],
    'includes': [
        "tkinter",
        "pyautogui",
        "pyperclip",
        "PIL",
        "Quartz",
        "AppKit",
        "Foundation",
        "objc",
    ],
    'excludes': ['rubicon'],
    'plist': {
        'CFBundleName': 'LINE 自動發送工具',
        'CFBundleIdentifier': 'com.example.linesender',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
    },
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
