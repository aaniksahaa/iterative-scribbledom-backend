# server.py
from flask import Flask
from flask_socketio import SocketIO, emit
import os
import time
import subprocess
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

check_started = False

@socketio.on('connect')
def handle_connect():
    global check_started
    print('Client connected')
    if(not check_started):
        check_started = True
        socketio.start_background_task(check_updates)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('run_iteration')
def handle_run_iteration(data):
    for i in range(1000):
        with open('updates.log', 'a') as file:
            file.write(f'\n\n{i}\n\n')
        time.sleep(8)

def check_updates():
    interval = 5
    print('check running')
    try:
        with open('updates.log', 'r') as file:
            processed = 0
            t = 0
            while True:
                #print(f'checking at t = {t}')

                file.seek(0,2)

                size = file.tell()

                if(processed < size):
                    file.seek(processed)
                    updates = file.read()

                    print(f'update found here at t = {t}')
                    print(f"Sending update to clients: {updates}")
                    socketio.emit('progress_update', {'progress': updates})

                    processed = size

                time.sleep(interval)
                t += interval

    except Exception as e:
        print(f"Error reading updates: {e}")
        time.sleep(1)

if __name__ == '__main__':
    with open('updates.log', 'w') as log_file:
        log_file.write('')
    print('\nlog file cleared')
    print('\nsocketio running\n')
    socketio.run(app, debug=False)
    
