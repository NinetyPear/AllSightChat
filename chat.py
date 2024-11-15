import openai
from config import CURRENT_VERSION, AccessKey_5150, UserID_5150, LIVE
import customtkinter as ctk
import tkinter as tk
import requests
import zipfile
import os
import sys
import datetime  # Import for timestamp
from io import BytesIO
import json  # Import for JSON format
from Crypto.Cipher import AES
import base64
import threading


# Define the global variable to store incoming message chunks for streaming
message_chunks = []
chat_log = []  # To store the chat log

def verify_access():
    try:
        response = requests.post(
            "https://5150leagues.com/api/AllSight_SecretKey.php",
            data={
                "UserID_5150": UserID_5150,
                "AccessKey_5150": AccessKey_5150,
            }
        )

        response_json = response.json()
        #print("Server response:", response_json)

        if response.status_code == 200 and response_json.get("status") == "success":
            #print("Access verified successfully.")

            # Get the encrypted OpenAI API key and IV from the response
            encrypted_key_base64 = response_json.get("encrypted_key")
            iv_base64 = response_json.get("iv")

            # Check if the required keys are present
            if not encrypted_key_base64 or not iv_base64:
                #print("Error: Missing 'encrypted_key' or 'iv' in the response.")
                access_denied_label.config(text="Access Denied: Server error.", fg="#ff4d4d")
                return False

            # Decrypt the OpenAI API key (using the previously working decryption code)
            encryption_key = bytes.fromhex("000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f")
            encrypted_key = base64.b64decode(encrypted_key_base64)
            iv = base64.b64decode(iv_base64)
            cipher = AES.new(encryption_key, AES.MODE_CBC, iv)
            decrypted_key = cipher.decrypt(encrypted_key)

            padding_length = decrypted_key[-1]
            if padding_length < 1 or padding_length > 16:
                #print("Invalid padding length.")
                access_denied_label.config(text="Access Denied: Decryption error.", fg="#ff4d4d")
                return False
            decrypted_key = decrypted_key[:-padding_length].decode('utf-8').strip()

            # Set the OpenAI API key
            openai.api_key = decrypted_key

            # Update the connection status and enable the send button
            if LIVE:
                connection_status_label.config(text="Connected to OpenAI & 5150")
            else:
                connection_status_label.config(text="Debug Mode (OpenAI disabled)")
            
            send_button.configure(state="normal")  # Enable the send button
            return True
        else:
            #print("Access verification failed.")
            access_denied_label.config(text="Access Denied. Please create a Secret Key in your 5150 Leagues account to proceed!", fg="#ff4d4d")
            return False

    except requests.exceptions.RequestException as e:
        #print(f"Error during access verification: {e}")
        access_denied_label.config(text="Access denied due to connection error.", fg="#ff4d4d")
        return False
    except Exception as e:
        #print(f"Error during decryption: {e}")
        access_denied_label.config(text="Decryption error.", fg="#ff4d4d")
        return False

# Initialize custom tkinter and set appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Create the root window
root = ctk.CTk()
root.title("AllSight")
root.iconbitmap("icon.ico")  # Path to your .ico file
root.geometry("510x600")

# Labels for update and access verification status (define these early)
connection_status_label = tk.Label(root, text="", bg="#1e1e1e", fg="#82e0aa", font=("Helvetica Neue", 10))
connection_status_label.pack(side="bottom", fill="x", pady=5)  # Connection status above update label

access_denied_label = tk.Label(root, text="", bg="#1e1e1e", fg="#ff4d4d", font=("Helvetica Neue", 10))
access_denied_label.pack(side="bottom", fill="x")  # Access denied label at the very bottom

update_label = tk.Label(root, text="Checking for updates...", bg="#1e1e1e", fg="#82e0aa", font=("Helvetica Neue", 10))
update_label.pack(side="bottom", fill="x", pady=5)  # Update label just above access denied label

######################## Message Box ########################

# Chat Textbox for displaying the entire chat history with a scrollbar
chat_textbox = tk.Text(root, wrap="word", bg="#333333", fg="white", font=("Helvetica Neue", 12), padx=10, pady=10)
chat_textbox.pack(fill="both", expand=True, padx=10, pady=10)

# Scrollbar for the chat_textbox
scrollbar = tk.Scrollbar(chat_textbox, orient="vertical", command=chat_textbox.yview)
chat_textbox.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")

# Make the chat_textbox read-only but selectable
chat_textbox.configure(state="disabled")

# Frame to hold the input field and send button at the bottom
input_frame = tk.Frame(root, bg="#333333")
input_frame.pack(fill="x", pady=5)

# Entry field for user input
entry = ctk.CTkEntry(input_frame, font=("Helvetica Neue", 12))
entry.pack(side="left", fill="x", padx=(10, 5), pady=10, expand=True)

# Send button
send_button = ctk.CTkButton(input_frame, text="Send", font=("Helvetica Neue", 12), command=lambda: send_message())
send_button.pack(side="right", padx=(5, 10), pady=10)

######################## END: Message Box ########################


# Call verify_access and display access denied message if necessary
if not verify_access():
    send_button.configure(state="disabled")  # Ensure button is disabled if access denied
else:
    send_button.configure(state="normal")  # Enable button if access is verified

def send_log_to_endpoint():
    try:
        # Define the endpoint URL (replace with your actual endpoint)
        url = "https://5150leagues.com/api/save_chat_log.php"

        # Convert chat log to JSON format
        chat_log_json = json.dumps(chat_log)

        # Construct the payload with chat log and access key
        payload = {
            "user_id": UserID_5150,
            "AccessKey_5150": AccessKey_5150,  # Include Access Key for verification
            "chat_log": chat_log_json
        }

        # Send the POST request with the chat log and access key
        response = requests.post(url, data=payload)  # Using data instead of json for plain POST data

        # Print the raw response text for debugging
        print("Server response:", response.text)

        # Check if the request was successful
        if response.status_code == 200 and response.json().get("status") == "success":
            print("Chat log successfully sent to the server.")
        else:
            print(f"Failed to send chat log. Status Code: {response.status_code}")
            print("Response:", response.text)
    except requests.RequestException as e:
        print(f"Error sending chat log to the server: {e}")

# Function to check for updates
def check_for_updates():
    url = f"https://api.github.com/repos/NinetyPear/AllSightChat/tags"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            latest_tag = response.json()[0]["name"]  # Get the name of the latest tag
            print(f"Latest version found: {latest_tag}")
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

# Function to get a response from OpenAI API with streaming
def get_ai_response(prompt):
    if LIVE:
        try:
            response_text = ""
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            # Collect message chunks and form the response
            for chunk in response:
                message_chunk = chunk['choices'][0]['delta'].get('content', '')
                if message_chunk:
                    response_text += message_chunk
            return response_text
        except Exception as e:
            return "Error: " + str(e)
    else:
        # Mock response for testing
        print("OpenAI disabled: Using mock response.")
        return "This is a test response to simulate OpenAI output."

# Function to fetch AI response in a separate thread
def fetch_response_in_background(user_input):
    response = get_ai_response(user_input)  # Get actual response from OpenAI API
    
    # Display the AI response in the main thread (UI updates should be in the main thread)
    root.after(0, lambda: display_message("AllSight", response))

# Function to handle user input and send message
def send_message(event=None):
    user_input = entry.get()
    if user_input.strip() == "":
        return  # Don't send empty messages

    display_message("You", user_input)  # Display the user message
    entry.delete(0, "end")  # Clear entry after sending
    
    # Start fetching AI response in a new thread
    threading.Thread(target=fetch_response_in_background, args=(user_input,), daemon=True).start()

# Function to display messages in a single textbox
def display_message(sender, message):
    # Enable the Text widget to insert new text
    chat_textbox.configure(state="normal")
    
    # Format the message
    formatted_message = f"{sender}: {message}\n\n"
    
    # Insert the message at the end
    chat_textbox.insert("end", formatted_message)
    
    # Apply color based on the sender
    if sender == "You":
        start_index = chat_textbox.index("end - 3 lines linestart")
        end_index = chat_textbox.index("end - 1 line lineend")
        chat_textbox.tag_add("You", start_index, end_index)
        chat_textbox.tag_config("You", foreground="cyan")
    elif sender == "AllSight":
        start_index = chat_textbox.index("end - 3 lines linestart")
        end_index = chat_textbox.index("end - 1 line lineend")
        chat_textbox.tag_add("AllSight", start_index, end_index)
        chat_textbox.tag_config("AllSight", foreground="lightgreen")

    # Make the Text widget read-only again and scroll to the bottom
    chat_textbox.configure(state="disabled")
    chat_textbox.see("end")

# Start the update check
update_in_background()

# Focus entry field on start
entry.focus_set()
entry.bind("<Return>", send_message)

# Check if labels are empty and hide if they are
if not connection_status_label["text"]:
    connection_status_label.pack_forget()

if not access_denied_label["text"]:
    access_denied_label.pack_forget()

if not update_label["text"]:
    update_label.pack_forget()

# Add the function to send log when closing the application
def on_closing():
    send_log_to_endpoint()  # Send log before closing
    root.destroy()

# Bind the close event
root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the main loop
root.mainloop()
