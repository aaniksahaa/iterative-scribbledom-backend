# server.py
from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
import os
import time
import subprocess
import threading
import json
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

def validate_preprocessed_data(dataset, sample_name):
    """Validate the directory structure under preprocessed_data/dataset/sample_name."""
    preprocessed_dir = os.path.join('preprocessed_data', dataset, sample_name)
    
    if not os.path.exists(preprocessed_dir):
        print(f'\nValidation failed: {preprocessed_dir} does not exist\n')
        return False

    # Define the required subdirectories for each sample
    expected_subdirs = [
        'Coordinates',
        # 'manual_scribble',
        'Principal_Components/CSV',
        'reading_h5',
        'reading_h5/spatial'
    ]

    missing_items = []

    # Check for the existence of each required subdirectory
    for subdir in expected_subdirs:
        full_path = os.path.join(preprocessed_dir, subdir)
        if not os.path.exists(full_path):
            missing_items.append(f"Directory: {full_path}")

    if missing_items:
        print(f'\nValidation failed: Missing items - {missing_items}\n')
        return False

    print(f'\nValidation successful for {preprocessed_dir}\n')
    return True

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

# new socket route for setting the current dataset and running the Rscript
@socketio.on('set_data')
def handle_set_data(data):
    if check_flag(SERVER_LOCKED):
        print('\n\nREQUEST REFUSED because SERVER is LOCKED\n\n')
        socketio.emit('error')
        return

    try:
        # Extract the required parameters
        space_ranger_output_directory = data['space_ranger_output_directory']
        dataset = data['dataset']
        sample_name = data['sample']
        samples = [sample_name]

        # Create the JSON configuration
        config = {
            "preprocessed_data_folder": "preprocessed_data",
            "matrix_represenation_of_ST_data_folder": "matrix_representation_of_st_data",
            "model_output_folder": "model_outputs",
            "final_output_folder": "final_outputs",
            "space_ranger_output_directory": space_ranger_output_directory,
            "dataset": dataset,
            "samples": samples,
            "technology": "visium",
            "n_pcs": 15,
            "n_cluster_for_auto_scribble": 2,
            "schema": "mclust",
            "max_iter": 300,
            "nConv": 1,
            "seed_options": [4],
            "alpha_options": [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95],
            "beta_options": [0.25, 0.3, 0.35, 0.4],
            "lr_options": [0.1]
        }

        # Define the path to save the JSON file
        # config_dir = os.path.join('IterativeScribbleDom', 'configs', sample_name)
        config_dir = os.path.join('configs', sample_name)
        os.makedirs(config_dir, exist_ok=True)  # Create the directory if it doesn't exist
        config_file_path = os.path.join(config_dir, f'{sample_name}_config_mclust.json')

        # Save the JSON file
        with open(config_file_path, 'w') as f:
            json.dump(config, f, indent=4)
        print(f'\nConfiguration file saved at: {config_file_path}\n')

        # Run the bash command
        # bash_command = f"sudo Rscript get_genex_data_from_10x_h5.R {config_file_path}"
        bash_command = f"sudo Rscript get_genex_data_from_10x_h5.R {config_file_path}"
        print(f'\nRunning command: {bash_command}\n')

        process = subprocess.Popen(bash_command, shell=True)
        process.wait()

        ok = (process.returncode == 0)

        # ok = True

        # Check if the command executed successfully
        if ok:
            # Validate the preprocessed data folder structure
            if validate_preprocessed_data(dataset, sample_name):
                create_folder_if_not_exists(os.path.join('final_outputs', dataset, sample_name))
                create_folder_if_not_exists(os.path.join('preprocessed_data', dataset, sample_name, 'manual_scribble'))
                print('\nRscript executed successfully and preprocessed data validated\n')
                socketio.emit('data_set_success', {'message': 'Data set and processed successfully'})
            else:
                print('\nRscript executed but preprocessed data validation failed\n')
                socketio.emit('error', {'message': 'Rscript executed but preprocessed data structure is incomplete'})
        else:
            print('\nError executing Rscript\n')
            socketio.emit('error', {'message': 'Failed to execute Rscript'})

    except Exception as e:
        print(f'\nError in set_data: {e}\n')
        socketio.emit('error', {'message': f'Error processing set_data: {str(e)}'})

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