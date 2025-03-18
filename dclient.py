# client.py
import socketio
import time

# Initialize the SocketIO client
sio = socketio.Client()

# Define event handlers for socket events
@sio.event
def connect():
    print("Connected to the server!")
    # Once connected, send a set_data request
    send_set_data()

@sio.event
def disconnect():
    print("Disconnected from the server!")

@sio.event
def data_set_success(data):
    print(f"Success: {data['message']}")

@sio.event
def error(data):
    print(f"Error: {data.get('message', 'Unknown error occurred')}")

@sio.event
def progress_update(data):
    print(f"Progress update: {data['progress']}")

def send_set_data():
    # Sample data to send in the set_data request
    data = {
        "space_ranger_output_directory": "raw_gene_x",
        "dataset": "cancers",
        "sample": "hbc_b1s1-dummy"
    }
    print(f"Sending set_data request with data: {data}")
    sio.emit('set_data', data)

if __name__ == '__main__':
    # Connect to the server (adjust the URL/port if needed)
    server_url = "http://localhost:5000"  # Default Flask-SocketIO port
    try:
        sio.connect(server_url)
        # Keep the client running to listen for events
        sio.wait()
    except Exception as e:
        print(f"Failed to connect to the server: {e}")