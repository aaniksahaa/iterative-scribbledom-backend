import re 
import os 
import pickle
import json 

SERVER_UTIL_DIR = 'server_utils'

# FLAG NAMES

PROCESS_ENDED = 'process_ended'
ABORT = 'abort'
SUCCESS = 'success'
SERVER_LOCKED = "server_locked"
RUN_ID = "run_id"

# CONSOLE INPUTS

def write_pickle(dir, filename, obj):
    filepath = os.path.join(dir, filename)
    with open(filepath, 'wb') as f:
        pickle.dump(obj, f)

def read_pickle(dir, filename):
    filepath = os.path.join(dir, filename)
    with open(filepath, 'rb') as f:
        obj = pickle.load(f)
    return obj

def read_txt(dir, filename):
    filepath = os.path.join(dir, filename)
    with open(filepath, 'r') as f:
        text = f.read()
    return text

def write_txt(dir, filename, text):
    filepath = os.path.join(dir, filename)
    with open(filepath,'w') as f:
        f.write(text)

def write_file(dir, filename, content):
    filepath = os.path.join(dir, filename)
    with open(filepath,'w') as f:
        f.write(content)

def read_json(dir, filename):
    filepath = os.path.join(dir, filename)
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data

def write_json(dir, filename, j):
    filepath = os.path.join(dir, filename)
    with open(filepath,'w') as f:
        f.write(json.dumps(j,indent=4))

def file_exists(directory, filename):
    """Check if a file exists in the given directory."""
    file_path = os.path.join(directory, filename)
    return os.path.isfile(file_path)

def check_flag(flag: str):
    if(file_exists(SERVER_UTIL_DIR, 'flags.json')):
        j = read_json(SERVER_UTIL_DIR, 'flags.json')
        return j[flag]

def update_flag(flag: str, value: bool):
    if(file_exists(SERVER_UTIL_DIR, 'flags.json')):
        j = read_json(SERVER_UTIL_DIR, 'flags.json')
        j[flag] = value
        write_json(SERVER_UTIL_DIR,'flags.json',j)

def display(*args):
    text = ''.join([str(arg) for arg in args]) + '\n'
    print(text)
    with open('updates.log','a') as f:
        f.write(text)

