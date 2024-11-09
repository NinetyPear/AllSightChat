import openai
import config
import customtkinter as ctk
import tkinter as tk
import requests
import zipfile
import os
import sys
from io import BytesIO

# Import CURRENT_VERSION from config
from config import CURRENT_VERSION

# GitHub repository details
repo_owner = "NinetyPear"
repo_name = "AllSightChat"

# Define the global variable to store incoming message chunks for streaming
message_chunks = []

# Function to get a response from OpenAI API with streaming
def get_ai_response(prompt):
    try:
        response_text = ""
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            stream=True  # Enable streaming for real-time response
        )

        for chunk in response:
            message_chunk = chunk['choices'][0]['delta'].get('content', '')
            if message_chunk:
                message_chunks.append(message_chunk)  # Add the chunk to the list
                response_text += message_chunk
        return response_text
    except Exception as e:
        return "Error: " + str(e)

# Function to fetch AI response in a separate thread
def fetch_response_in_background(prompt):
    global message_chunks
    message_chunks.clear()  # Clear previous message chunks
    response_text = get_ai_response(prompt)
    display_message("AllSight", response_text)

# Function to handle user input and send message
def send_message(event=None):
    user_input = entry.get()
    if user_input.strip() == "":
        return  # Don't send empty messages

    display_message("You", user_input)
    entry.delete(0, "end")
    
    # Start fetching AI response in a new thread
    fetch_response_in_background(user_input)

# Function to display messages with rounded bubbles using Canvas
# Function to display messages with rounded bubbles using Canvas
# Function to display messages with rounded bubbles using Canvas
# Function to display messages with rounded bubbles using Canvas
# Function to display messages with rounded bubbles using Canvas
def display_message(sender, message):
    # Create a frame for the message bubble with no padding
    bubble_frame = tk.Frame(messages_frame, bg="#1e1e1e", pady=0)
    bubble_frame.grid(sticky="w" if sender == "AllSight" else "e", padx=10)  # Using grid for better control

    # Configure colors and alignment based on sender
    bubble_color = "#2a2d32" if sender == "You" else "#2f3136"
    text_color = "#4da6ff" if sender == "You" else "#82e0aa"
    justify = "e" if sender == "You" else "w"

    # Adjust the text and bubble height dynamically based on the message length
    max_line_length = 45  # Number of characters before wrapping to the next line
    lines = (len(message) // max_line_length) + 1
    bubble_height = 20 + (lines * 18)  # Adjust bubble height based on the line count

    # Create a Canvas with height adjusted to message content
    bubble_canvas = tk.Canvas(bubble_frame, bg="#1e1e1e", highlightthickness=0, width=380, height=bubble_height)
    bubble_canvas.grid(row=0, column=0)  # Position the canvas inside the frame with grid

    # Draw rounded rectangle for the bubble effect
    x1, y1, x2, y2, radius = 5, 5, 380, bubble_height, 15
    bubble_canvas.create_arc((x1, y1, x1 + radius, y1 + radius), start=90, extent=90, fill=bubble_color, outline=bubble_color)
    bubble_canvas.create_arc((x2 - radius, y1, x2, y1 + radius), start=0, extent=90, fill=bubble_color, outline=bubble_color)
    bubble_canvas.create_arc((x1, y2 - radius, x1 + radius, y2), start=180, extent=90, fill=bubble_color, outline=bubble_color)
    bubble_canvas.create_arc((x2 - radius, y2 - radius, x2, y2), start=270, extent=90, fill=bubble_color, outline=bubble_color)
    bubble_canvas.create_rectangle((x1 + radius / 2, y1, x2 - radius / 2, y2), fill=bubble_color, outline=bubble_color)
    bubble_canvas.create_rectangle((x1, y1 + radius / 2, x2, y2 - radius / 2), fill=bubble_color, outline=bubble_color)

    # Display the message text with wrapping inside the bubble
    bubble_canvas.create_text(x1 + 10, y1 + 5, text=f"{sender}: {message}", fill=text_color, font=("Helvetica Neue", 12), anchor="nw", width=350)

    # Auto-scroll to the bottom of the canvas
    messages_canvas.update_idletasks()
    messages_canvas.yview_moveto(1)


# Function to check for updates
def check_for_updates():
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/tags"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            latest_tag = response.json()[0]["name"]  # Get the name of the latest tag
            return latest_tag
        else:
            print(f"Failed to check for updates. Status Code: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Error checking for updates: {e}")
        return None

# Function to download the latest release
def download_latest_release(version):
    url = f"https://github.com/{repo_owner}/{repo_name}/archive/refs/tags/{version}.zip"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
                zip_ref.extractall(".")
            print("Update downloaded and extracted.")
        else:
            print("Failed to download update.")
    except requests.RequestException as e:
        print(f"Error downloading update: {e}")

# Function to restart the program
def restart_program():
    os.execl(sys.executable, sys.executable, *sys.argv)

# Function to update the program based on the check
def update_program():
    latest_version = check_for_updates()
    if latest_version and latest_version != CURRENT_VERSION:
        print(f"A new version ({latest_version}) is available! Updating...")
        update_label.config(text=f"A new version ({latest_version}) is available! Updating...")
        download_latest_release(latest_version)
        restart_program()
    else:
        update_label.config(text="You’re using the latest version.")
        print("You’re using the latest version.")

# Function to run update check in the main thread without blocking UI
def update_in_background():
    root.after(5000, update_program)  # Call update_program after 5 seconds to avoid blocking UI

# Initialize custom tkinter and set appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Create the root window
root = ctk.CTk()
root.title("Chat with AllSight")
root.geometry("500x600")

# Create a frame to hold messages and scrollbar together
messages_frame_wrapper = tk.Frame(root)
messages_frame_wrapper.pack(fill="both", expand=True)

# Create a canvas to hold the scrollable messages frame
messages_canvas = tk.Canvas(messages_frame_wrapper, bg="#1e1e1e", bd=0, highlightthickness=0)
messages_canvas.pack(side="left", fill="both", expand=True)

# Add a scrollbar to the canvas
scrollbar = tk.Scrollbar(messages_frame_wrapper, command=messages_canvas.yview)
scrollbar.pack(side="right", fill="y")

messages_canvas.configure(yscrollcommand=scrollbar.set)

# Container frame inside the canvas for messages
messages_frame = tk.Frame(messages_canvas, bg="#1e1e1e")
messages_canvas.create_window((0, 0), window=messages_frame, anchor="nw")

# Update scroll region when messages are added
def on_frame_configure(event):
    messages_canvas.configure(scrollregion=messages_canvas.bbox("all"))

messages_frame.bind("<Configure>", on_frame_configure)

# Frame to hold the input field and send button at the bottom
input_frame = tk.Frame(root, bg="#1e1e1e")
input_frame.pack(fill="x", pady=5)

# User input field in the input frame
entry = ctk.CTkEntry(input_frame, font=("Helvetica Neue", 12))
entry.pack(side="left", fill="x", padx=(10, 5), pady=10, expand=True)

# Send button in the input frame
send_button = ctk.CTkButton(input_frame, text="Send", command=send_message, font=("Helvetica Neue", 12))
send_button.pack(side="right", padx=(5, 10), pady=10)

# Create a label to display the update status at the bottom
update_label = tk.Label(root, text="Checking for updates...", bg="#1e1e1e", fg="#82e0aa", font=("Helvetica Neue", 10))
update_label.pack(side="bottom", fill="x", pady=5)

# Focus entry field on start
entry.focus_set()

# Bind Enter key to send message
entry.bind("<Return>", send_message)

# Start the update check
update_in_background()

# Start the main loop
root.mainloop()
