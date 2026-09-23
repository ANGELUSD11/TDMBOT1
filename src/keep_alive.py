from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running!"

def run():
    from waitress import serve
    serve(app, host='0.0.0.0', port=8080, _quiet=True)

def keep_alive():
    t = Thread(target=run)
    t.start()
