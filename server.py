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

# @socketio.on('start_task')
# def handle_start_task():
#     print('Start task command received')
#     # Assume client.py writes updates to updates.log
#     subprocess.Popen(['python', 'client.py'])

@socketio.on('run_iteration')
def handle_run_iteration(data):
    iter_no = data['iter_no']
    print(f'Client requested to run iteration {iter_no}')
    # Assume client.py writes updates to updates.log

    batch_file = 'run_hbc_b1s1.bat'
    curr_iteration = f'{iter_no}'
    n_max_scribble_file = '10'

    command = [batch_file, curr_iteration, n_max_scribble_file]

    subprocess.Popen([batch_file, curr_iteration, n_max_scribble_file])

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
                    #print("updates : ", updates)
                    print(f"Sending update to clients: {updates}")
                    socketio.emit('progress_update', {'progress': updates})

                    processed = size

                time.sleep(interval)
                t += interval

    except Exception as e:
        print(f"Error reading updates: {e}")
        time.sleep(1)

if __name__ == '__main__':
    print('log file cleared')
    with open('updates.log', 'w') as log_file:
        log_file.write('')
    #socketio.start_background_task(check_updates)
    #threading.Thread(target=check_updates)
    print('socketio running')
    socketio.run(app, debug=False)
    # Start a thread to continuously check for updates
    
