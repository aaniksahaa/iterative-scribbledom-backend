import sys

def write_to_log(entry):
    with open('updates.log', 'a') as log_file:
        log_file.write(entry + '\n')

if __name__ == "__main__":
    ############################################

    # THIS CODE IS ADDED FOR DESKTOP APP SERVER

    from util import *
    if check_flag(ABORT) or check_flag(SERVER_LOCKED):
        exit()

    ############################################

    if len(sys.argv) != 2:
        print("Usage: python log_writer.py \"Your log entry\"")
        sys.exit(1)

    prefix = "========================================\n\n"
    
    log_entry = prefix + sys.argv[1] + "\n\n"
    write_to_log(log_entry)
    print(log_entry)
