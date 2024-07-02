import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import subprocess
import json

# Function to save default branch setting to a JSON file
def save_settings(default_branch):
    with open('settings.json', 'w') as f:
        json.dump({'default_branch': default_branch}, f)

# Function to load default branch setting from a JSON file
def load_settings():
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
            return settings['default_branch']
    except FileNotFoundError:
        return None

# Function to update the default branch setting
def update_default_branch(*args):
    default_branch = default_branch_var.get()
    save_settings(default_branch)
    messagebox.showinfo("Settings", f"Default branch set to {default_branch}")

# Function to handle push operation
def git_push():
    commit_message = commit_entry.get()
    default_branch = load_settings()
    if commit_message:
        root.destroy()
        try:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            subprocess.run(["git", "push", "-u", "origin", default_branch], check=True)
        except subprocess.CalledProcessError as e:
            print('\nUnexpected Error: ' + e)
    else:
        messagebox.showerror("Error", "Please enter a commit message.")

# Initialize Tkinter window
root = tk.Tk()
root.title("Git Committer")







# Create style for buttons
style = ttk.Style()
style.configure('Custom.TButton', background='black', foreground='black', font=('Helvetica', 12))

# Frame for Commit Message
commit_frame = tk.Frame(root)
commit_frame.pack(padx=10, pady=5, fill="x")

commit_label = tk.Label(commit_frame, text="Commit Message:")
commit_label.grid(row=0, column=0, padx=5, pady=20)

commit_entry = tk.Entry(commit_frame, font=('Helvetica', 12), width=48)
commit_entry.grid(row=0, column=1, padx=5, pady=20, sticky="ew")
commit_entry.config(highlightbackground='black', highlightcolor='black', highlightthickness=1)

commit_entry.insert(0, 'a')

# Frame for Settings
settings_frame = tk.Frame(root)
settings_frame.pack(padx=10, pady=5, fill="x")

default_branch_label = tk.Label(settings_frame, text="Default Branch:")
default_branch_label.grid(row=0, column=0, padx=5, pady=3)

default_branch = load_settings()
default_branch_var = tk.StringVar(value=default_branch)
default_branch_entry = tk.Entry(settings_frame, textvariable=default_branch_var, font=('Helvetica', 12))
default_branch_entry.grid(row=0, column=1, padx=20, pady=3)
default_branch_entry.config(highlightbackground='black', highlightcolor='black', highlightthickness=1)

update_button = ttk.Button(settings_frame, text="Update", command=update_default_branch, style='Custom.TButton')
update_button.grid(row=0, column=2, padx=122, pady=3)

# Push button
push_button = ttk.Button(root, text="Push", command=git_push, style='Custom.TButton')
push_button.pack(pady=30)

# Result label
result_label = tk.Label(root, text="")
result_label.pack(pady=5)





# Calculate the position to center the window
window_width = 600
window_height = 210
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x_coordinate = (screen_width - window_width) // 2
y_coordinate = (screen_height - window_height) // 2 - 50

# Set the geometry of the window to center it
root.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")



root.mainloop()
