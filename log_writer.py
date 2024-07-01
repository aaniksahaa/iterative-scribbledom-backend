import sys

def write_to_log(entry):
    with open('updates.log', 'a') as log_file:
        log_file.write(entry + '\n')

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python log_writer.py \"Your log entry\"")
        sys.exit(1)

    prefix = "========================================\n\n"
    
    log_entry = prefix + sys.argv[1] + "\n\n"
    write_to_log(log_entry)
    print(log_entry)
