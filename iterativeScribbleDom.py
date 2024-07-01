import os
import subprocess


n_iterations = 10
n_max_scribble_files = 10

def check_if_file_exists(filename):
    if os.path.isfile(filename):
        return True
    else:
        return False

def get_thefile_from_prompt():
    is_done = 'rand'
    while is_done!= 'y' and is_done!='n':
        is_done = input("y/n : y=gave scribble, n=exit >>>  ")
        if is_done!= 'y' and is_done!= 'n':
            print("please enter y or n")

        if is_done == 'y':
            filename = f'preprocessed_data/cancers/hbc_b1s1/manual_scribble/manual_scribble_{i}.csv'
            if not check_if_file_exists(filename):
                print(f"file {filename} does not exist")
                is_done = "rand"
    return is_done

for i in range(1, 1 + n_iterations):
    print(f"\n\nAdd 'manual_scrible_{i}.csv' in directory 'preprocessed_data/cancers/hbc_b1s1/manual_scribble'")
    is_done = get_thefile_from_prompt()

    if is_done == 'n':
        print("\n\nexiting...")
        exit()

    print("-------------Processing--------------")
    os.system("chmod +x run_hbc_b1s1.sh")
    os.system(f"./run_hbc_b1s1.sh {i} {n_max_scribble_files}")

    # Rename the final_out.png to final_out_{i}.png
    filePath = "final_outputs/cancers/hbc_b1s1/expert/final_out.png"
    os.system(f"mv {filePath} {filePath[:-4]}_{i}.png")
