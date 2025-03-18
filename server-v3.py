# server.py
from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
import os
import time
import subprocess
import threading
from util import * 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

running_process = None 

check_started = False


processed_bytes = 0

lock_time = 60

def write_abort():
    clear_log()
    lock_time
    print('\n\nABORTING ALREADY RUNNING MODELS (if any)\n')
    update_flag(ABORT,True)
    # lock the server if abrupt abort happens
    print(f'\nLOCKING SERVER for {lock_time} seconds\n\n')
    update_flag(SERVER_LOCKED,True)
    time.sleep(lock_time)
    update_flag(SERVER_LOCKED,False)
    print(f'\nRELEASING LOCK ON SERVER\n\n')

def clear_log():
    global processed_bytes
    update_flag(SERVER_LOCKED,True)
    N_TRIALS = 100
    ok = False
    for _ in range(N_TRIALS):
        try:
            with open('updates.log', 'w') as log_file:
                log_file.write('')
            print('\nlog file cleared')
            ok = True
            break
        except PermissionError:
            print('\nError: Permission denied when trying to clear the log file.')
        except FileNotFoundError:
            print('\nError: The log file was not found.')
        except Exception as e:
            print(f'\nAn unexpected error occurred: {e}')
        time.sleep(1)
    update_flag(SERVER_LOCKED,False)
    processed_bytes = 0
    return ok

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
    print(f'\n\nRunning Process Ended = {check_flag(PROCESS_ENDED)}\n\n')
    if (not check_flag(PROCESS_ENDED)) and (not check_flag(SERVER_LOCKED)):
        write_abort()

@socketio.on('run_iteration')
def handle_run_iteration(data):
    if check_flag(SERVER_LOCKED):
        print('\n\nREQUEST REFUSED because SERVER is LOCKED\n\n')
        socketio.emit('error')
        return
    cleared = clear_log()
    if not cleared:
        print('\n\nSERVER ERROR\n\n')
        socketio.emit('error')
        return

    update_flag(ABORT,False)
    update_flag(PROCESS_ENDED,False)

    curr_id = check_flag(RUN_ID)+1
    update_flag(RUN_ID,curr_id)

    iter_no = data['iter_no']
    position_path = data['position_path']

    print(f'Client requested to run iteration {iter_no}')
    # Assume client.py writes updates to updates.log

    batch_file = 'run_hbc_b1s1.bat'

    if('human_dlpfc' in position_path.lower()):
        batch_file = 'run_human_dlpfc.bat'
    
    print(f'\n\nRUNNING {batch_file}\n\n')

    curr_iteration = f'{iter_no}'
    n_max_scribble_file = '10'

    command = [batch_file, curr_iteration, n_max_scribble_file]

    process = subprocess.Popen(command)
    process.wait()

    update_flag(PROCESS_ENDED, True)

    if not check_flag(ABORT) and check_flag(PROCESS_ENDED) and check_flag(RUN_ID)==curr_id:
        print('NOTIFYING SUCCESS to clients...')
        socketio.emit('success')

@socketio.on('abort')
def handle_abort():
    print('\n\nABORT REQUEST RECEIVED\n\n')
    write_abort()

def run_process(command):
    batch_file, curr_iteration, n_max_scribble_file = command

    try:
        process = subprocess.Popen([batch_file, curr_iteration, n_max_scribble_file])
        process.wait()
        socketio.emit('success')

    except Exception as e:
        print(f"Error running process: {e}")

def check_updates():
    global processed_bytes
    interval = 5
    print('check running')
    try:
        with open('updates.log', 'r') as file:
            processed_bytes = 0
            t = 0
            while True:
                if not check_flag(PROCESS_ENDED) and not check_flag(SERVER_LOCKED) and not check_flag(ABORT):
                    print(f'checking at t = {t}')

                    file.seek(0,2)

                    size = file.tell()

                    if(processed_bytes < size):
                        file.seek(processed_bytes)
                        updates = file.read()

                        if not check_flag(SERVER_LOCKED):
                            print(f'update found here at t = {t}')
                            print(f"Sending update to clients: \n{updates}")
                            socketio.emit('progress_update', {'progress': updates})

                        processed_bytes = size

                time.sleep(interval)
                t += interval

    except Exception as e:
        print(f"Error reading updates: {e}")
        time.sleep(1)

@app.route('/health-check', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'server_locked': check_flag(SERVER_LOCKED)})

if __name__ == '__main__':
    update_flag(ABORT, False)
    update_flag(SERVER_LOCKED,False)
    update_flag(RUN_ID, 0)
    update_flag(PROCESS_ENDED,True)
    clear_log()
    print('\nsocketio running\n')
    socketio.run(app, debug=False)
    
