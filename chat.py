import openai
from config import CURRENT_VERSION, AccessKey_5150, UserID_5150, LIVE, AI_MODEL
import customtkinter as ctk
import tkinter as tk
import requests
import zipfile
import os
import sys
from datetime import datetime
from io import BytesIO
import json  # Import for JSON format
from Crypto.Cipher import AES
import base64
import threading
import uuid
import tiktoken
import time

tokenizer = tiktoken.encoding_for_model(AI_MODEL)

# Define the global variable to store incoming message chunks for streaming
message_chunks = []
chat_log = []  # To store the chat log
total_tokens_used = 0
chat_sessions = {}

chat_session_id = str(uuid.uuid4())  # Generate a unique session ID for the chat session
#print(f"Chat Session ID: {chat_session_id}")
# Initialize custom tkinter and set appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Create the root window
root = ctk.CTk()
root.title("AllSight")
root.iconbitmap("icon.ico")  # Path to your .ico file
root.geometry("600x855")

######################## Chat Sessions and Message Box ########################
# Create a main frame to hold chat sessions and the message box
chat_area_frame = ctk.CTkFrame(
    root, 
    fg_color="#1e1e1e",  # Match the dark theme
    corner_radius=10,
    border_color="#333333",
    border_width=2
)
chat_area_frame.pack(fill="both", expand=True, padx=10, pady=10)

# Chat Sessions frame (placed at the top)
chat_sessions_frame = ctk.CTkFrame(
    chat_area_frame, 
    fg_color="#1e1e1e", 
    corner_radius=10,
    border_color="#333333",
    border_width=1,
    height=140  # Adjust height to fit canvas and scrollbar perfectly
)
chat_sessions_frame.pack(side="top", fill="x", padx=10, pady=(5, 15))

# Scrollable frame for session bubbles
bubble_canvas = tk.Canvas(
    chat_sessions_frame,
    bg="#1e1e1e",  # Match the frame background
    highlightthickness=0,
    height=110  # Adjust height for the session bubble area
)
bubble_canvas.pack(side="top", fill="x", padx=5, pady=(5, 0))  # Ensure padding matches the frame

bubble_scrollbar = ctk.CTkScrollbar(
    chat_sessions_frame,
    orientation="horizontal",
    command=bubble_canvas.xview,
    fg_color="#333333",
    button_color="#555555",
    button_hover_color="#777777"
)
bubble_scrollbar.pack(side="top", fill="x", padx=5, pady=(5, 10))  # Match the padding of the canvas

bubble_canvas.configure(xscrollcommand=bubble_scrollbar.set)

# Frame inside the canvas to hold the bubble elements
bubble_container = tk.Frame(bubble_canvas, bg="#1e1e1e")
bubble_canvas.create_window((0, 0), window=bubble_container, anchor="nw")

# Chat Message Box frame (below the chat sessions)
chat_frame = ctk.CTkFrame(
    chat_area_frame, 
    fg_color="#1e1e1e",  # Background color for the frame
    corner_radius=10,    # Rounded corners
    border_color="#333333",  # Border color
    border_width=2       # Border thickness
)
chat_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

# Chat Textbox inside the modern frame
chat_textbox = tk.Text(
    chat_frame, 
    wrap="word", 
    bg="#1e1e1e",       # Match frame background
    fg="white",         # Text color
    font=("Helvetica Neue", 12), 
    bd=0,               # Remove default border
    padx=10, pady=10,   # Add padding inside the textbox
    highlightthickness=0  # Remove highlight border
)
chat_textbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)

# Modern Scrollbar for the conversation box
scrollbar = ctk.CTkScrollbar(
    chat_frame, 
    orientation="vertical", 
    command=chat_textbox.yview, 
    fg_color="#333333",  # Scrollbar background
    button_color="#555555",  # Scroll button color
    button_hover_color="#777777"  # Hover effect for buttons
)
scrollbar.pack(side="right", fill="y", padx=(0, 5), pady=5)

# Attach the scrollbar to the chat textbox
chat_textbox.configure(yscrollcommand=scrollbar.set)

# Make the chat textbox read-only but selectable
chat_textbox.configure(state="disabled")

# Adjust the scroll region for the bubble canvas
def update_bubble_canvas():
    bubble_container.update_idletasks()
    bubble_canvas.configure(scrollregion=bubble_canvas.bbox("all"))

def deduplicate_chat_log(chat_log):
    """
    Deduplicates chat log entries while normalizing data types (dicts and strings).
    """
    unique_entries = []
    seen_messages = set()

    for entry in chat_log:
        if isinstance(entry, dict):
            sender = entry.get("sender", "Unknown")
            message = entry.get("message", "").strip()
        else:
            # Parse string entries into a standardized format
            if ": " in entry:
                sender, message = entry.split(": ", 1)
            else:
                sender, message = "Unknown", entry
            message = message.strip()

        # Create a unique identifier for deduplication
        unique_key = f"{sender}:{message}"

        if unique_key not in seen_messages:
            seen_messages.add(unique_key)
            unique_entries.append({
                "sender": sender,
                "message": message
            })

    return unique_entries

def populate_chat_sessions(chat_logs):
    """
    Dynamically populate the chat session bubbles with actual logs from the API response.
    """
    # Clear existing bubbles
    for widget in bubble_container.winfo_children():
        widget.destroy()

    # Iterate through the chat logs and create bubbles
    for log in chat_logs:
        session_id = log.get("ChatSession_id", "Unknown")
        raw_timestamp = log.get("timestamp", "No Timestamp")  # Extract raw timestamp

        # Format the timestamp
        formatted_timestamp = ""
        try:
            # Assuming the timestamp is in "YYYY-MM-DD HH:MM:SS" format
            dt_object = datetime.strptime(raw_timestamp, "%Y-%m-%d %H:%M:%S")
            formatted_timestamp = dt_object.strftime("%b %d, %Y, %I:%M %p")  # Example: "Nov 16, 2024, 12:30 PM"
        except ValueError:
            # If the format is unexpected, keep the raw timestamp
            formatted_timestamp = raw_timestamp

        # Session Bubble
        bubble = ctk.CTkFrame(
            bubble_container,
            fg_color="#2d2d2d",  # Darker modern background
            corner_radius=12,
            border_color="#444444",
            border_width=2,
            width=150,  # Compact size
            height=80
        )
        bubble.pack(side="left", padx=10, pady=5)

        # Session Title
        session_label = ctk.CTkLabel(
            bubble,
            text=f"Session\n{session_id}",
            text_color="#ffffff",
            font=("Helvetica Neue", 10, "bold"),
            justify="center"
        )
        session_label.pack(padx=5, pady=(8, 2))

        # Timestamp
        timestamp_label = ctk.CTkLabel(
            bubble,
            text=formatted_timestamp,  # Use the formatted timestamp
            text_color="#aaaaaa",
            font=("Helvetica Neue", 8),
            justify="center"
        )
        timestamp_label.pack(padx=5, pady=(0, 5))

        # Load Button
        load_button = ctk.CTkButton(
            bubble,
            text="Load",
            font=("Helvetica Neue", 9),
            fg_color="#007bff",
            text_color="white",
            hover_color="#0056b3",
            corner_radius=6,
            command=lambda s=session_id: load_chat_session(s)  # Call to load session
        )
        load_button.pack(pady=(0, 5))

    # Update the canvas scroll region
    update_bubble_canvas()

def fetch_and_populate_chat_sessions():
    """
    Fetch and populate chat sessions from the server.
    """
    try:
        # Fetch chat logs from the server
        url = "https://5150leagues.com/api/AllSight_GetLast_Chat.php"
        payload = {"user_id": UserID_5150, "AccessKey_5150": AccessKey_5150}
        response = requests.post(url, data=payload)
        response_json = response.json()

        if response.status_code == 200 and response_json.get("status") == "success":
            chat_logs = response_json.get("chat_logs", [])

            # Normalize and store each session
            for log in chat_logs:
                session_id = log["ChatSession_id"]
                chat_log = deduplicate_chat_log(log.get("chat_log", []))
                chat_sessions[session_id] = chat_log

            # Update the UI with fetched sessions
            populate_chat_sessions(chat_logs)
        else:
            print(f"Failed to fetch chat logs: {response_json.get('message', 'Unknown error')}")

    except Exception as e:
        print(f"Error fetching chat logs: {e}")

def load_chat_session(session_id):
    """
    Load and display the selected chat session in the chat message box.
    """
    try:
        if session_id not in chat_sessions:
            print(f"Session ID {session_id} not found.")
            return

        chat_log_data = chat_sessions[session_id]
        normalized_log = deduplicate_chat_log(chat_log_data)

        # Clear and prepare the chat message box
        chat_textbox.configure(state="normal")
        chat_textbox.delete("1.0", "end")

        # Populate the chat box with deduplicated and formatted messages
        for entry in normalized_log:
            sender = entry["sender"]
            message = entry["message"]

            formatted_message = f"{sender}: {message}\n\n"
            start_index = chat_textbox.index("end")
            chat_textbox.insert("end", formatted_message)

            # Apply color based on the sender
            if sender == "You":
                chat_textbox.tag_add("You", start_index, chat_textbox.index("end"))
                chat_textbox.tag_config("You", foreground="cyan")
            elif sender == "AllSight":
                chat_textbox.tag_add("AllSight", start_index, chat_textbox.index("end"))
                chat_textbox.tag_config("AllSight", foreground="lightgreen")
            else:
                chat_textbox.tag_add("Other", start_index, chat_textbox.index("end"))
                chat_textbox.tag_config("Other", foreground="white")

        # Reset the state of the text box
        chat_textbox.configure(state="disabled")
        chat_textbox.see("end")

    except Exception as e:
        print(f"Error loading chat session: {e}")


# Call populate_chat_sessions to test the layout
fetch_and_populate_chat_sessions()
######################## END: Chat Sessions and Message Box ########################

######################## User Input Section ########################
# Frame to hold the input field and send button (Modern Style)
input_frame = ctk.CTkFrame(
    root, 
    fg_color="#1e1e1e",  # Match the chat message box background
    corner_radius=10,    # Same rounded corners as chat_frame
    border_color="#333333", 
    border_width=2
)
input_frame.pack(fill="x", padx=10, pady=10)  # Add consistent margins

# Entry field for user input (Modern Style)
entry = ctk.CTkEntry(
    input_frame, 
    font=("Helvetica Neue", 12), 
    placeholder_text="Type your message here...", 
    height=35  # Adjust height for consistency
)
entry.pack(side="left", fill="x", padx=(10, 5), pady=10, expand=True)

# Send button (Modern Style)
send_button = ctk.CTkButton(
    input_frame, 
    text="Send", 
    font=("Helvetica Neue", 12), 
    fg_color="#007bff",  # Button background color
    hover_color="#0056b3",  # Button hover effect
    text_color="white", 
    corner_radius=8,  # Rounded corners for consistency
    command=lambda: send_message()
)
send_button.pack(side="right", padx=(5, 10), pady=10)
######################## END: User Input Section ########################

######################## Button Menu #############################
# Frame for the bottom buttons
bottom_button_frame = ctk.CTkFrame(
    root,
    fg_color="#1e1e1e",
    corner_radius=10,
    border_color="#333333",
    border_width=2
)
bottom_button_frame.pack(side="bottom", fill="x", padx=10, pady=10)

# Report Conversation Button
report_convo_button = ctk.CTkButton(
    bottom_button_frame,
    text="Report Conversation",
    font=("Helvetica Neue", 12),
    fg_color="#007bff",  # Button color (modern blue)
    text_color="white",
    hover_color="#0056b3",  # Darker hover color
    corner_radius=8,  # Rounded corners
    command=lambda: report_to_support("conversation")
)
report_convo_button.pack(side="left", padx=5, pady=5, expand=True)

# New Chat Button
def new_chat():
    """
    Clears the message box and resets the chat log.
    """
    global chat_log
    chat_log = []  # Reset the chat log
    chat_textbox.configure(state="normal")
    chat_textbox.delete("1.0", "end")  # Clear the message box
    chat_textbox.configure(state="disabled")  # Make it read-only again
    print("New chat started.")  # For debugging

new_chat_button = ctk.CTkButton(
    bottom_button_frame,
    text="New Chat",
    font=("Helvetica Neue", 12),
    fg_color="#28a745",  # Green button
    text_color="white",
    hover_color="#218838",
    corner_radius=8,  # Rounded corners
    command=new_chat
)
new_chat_button.pack(side="left", padx=5, pady=5, expand=True)

# Report Bug Button
report_bug_button = ctk.CTkButton(
    bottom_button_frame,
    text="Report Bug",
    font=("Helvetica Neue", 12),
    fg_color="#dc3545",  # Red button color
    text_color="white",
    hover_color="#c82333",  # Darker hover color
    corner_radius=8,  # Rounded corners
    command=lambda: report_to_support("bug")
)
report_bug_button.pack(side="left", padx=5, pady=5, expand=True)
######################## END: Button Menu ########################

######################## Labels #############################
# Create a frame to hold the status labels
status_frame = ctk.CTkFrame(root, fg_color="#1e1e1e", corner_radius=10)
status_frame.pack(side="bottom", fill="x", padx=10, pady=(5, 10))

# Label 1: Connection status to 5150 & OpenAI
connection_status_label = tk.Label(
    status_frame,
    text="",  # Will be updated dynamically
    bg="#1e1e1e",
    fg="#82e0aa",  # Default green color
    font=("Helvetica Neue", 10),
    anchor="w"  # Align text to the left
)
connection_status_label.pack(side="top", fill="x", padx=10, pady=(2, 2))

# Label 2: Checking for Updates/Version Status
update_status_label = tk.Label(
    status_frame,
    text="Checking for updates...",  # Default text
    bg="#1e1e1e",
    fg="#82e0aa",  # Default green color
    font=("Helvetica Neue", 10),
    anchor="w"
)
update_status_label.pack(side="top", fill="x", padx=10, pady=(2, 2))

######################## END: Labels #########################

# Function to dynamically update the connection status label (Label 1)
def update_connection_status(live_status, verification_status=True):
    """
    Updates the connection status label based on LIVE status and verification result.

    Args:
    live_status (bool): If True, indicates LIVE mode; otherwise, Debug mode.
    verification_status (bool): If True, verification is successful; otherwise, failed.
    """
    if not verification_status:
        connection_status_label.config(
            text="Verification Failed",
            fg="#ff4d4d"  # Red for failure
        )
    else:
        if live_status:
            connection_status_label.config(
                text="Connected to OpenAI & 5150",
                fg="#82e0aa"  # Green for success
            )
        else:
            connection_status_label.config(
                text="Debug Mode: OpenAI Disabled",
                fg="#ffaa00"  # Orange for debug mode
            )

def update_server_chat_log():
    """
    Sends the updated chat log to the server to synchronize with the stored log.
    """
    if not LIVE:
        print("Live mode is disabled. Skipping server log update.")
        return

    try:
        # Deduplicate the chat log to avoid duplicate entries
        unique_chat_log = deduplicate_chat_log(chat_log)

        # Convert chat log to JSON
        chat_log_json = json.dumps(unique_chat_log)

        # Define the endpoint URL
        url = "https://5150leagues.com/api/update_chat_log.php"  # Use an update endpoint

        # Construct the payload
        payload = {
            "user_id": UserID_5150,
            "AccessKey_5150": AccessKey_5150,
            "chat_log": chat_log_json,
            "chat_session_id": chat_session_id  # Use this to identify the record to update
        }

        # Send the POST request
        response = requests.post(url, data=payload)

        # Print the raw response for debugging
        print("Server response:", response.text)

        # Check if the request was successful
        if response.status_code == 200:
            response_json = response.json()
            if response_json.get("status") == "success":
                print("Chat log successfully updated on the server.")
            else:
                print(f"Failed to update chat log: {response_json.get('message', 'No message provided')}")
        else:
            print(f"Failed to update chat log. Status Code: {response.status_code}")
            print("Response:", response.text)
    except requests.RequestException as e:
        print(f"Error updating chat log on the server: {e}")
# Function to calculate the number of tokens in a message
def calculate_tokens(message):
    """
    Calculates the number of tokens in a message.
    """
    return len(tokenizer.encode(message))  # Ensure `tiktoken` is imported and set up

# Function to dynamically update the update status label (Label 2)
def update_version_status(status):
    """
    Updates the version status label dynamically.

    Args:
    status (str): Status message, e.g., "Checking for updates...", "Updating...", "You’re using the latest version."
    """
    update_status_label.config(text=status)
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
    url = f"https://github.com/NinetyPear/AllSightChat/archive/refs/tags/{version}.zip"
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
        update_version_status(f"A new version ({latest_version}) is available! Updating...")
        download_latest_release(latest_version)
        restart_program()
    else:
        update_version_status("You’re using the latest version.")
        print("You’re using the latest version.")

# Function to run update check in the main thread without blocking UI
def update_in_background():
    root.after(5000, update_program)
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
        # Debug: Print server response
        #print("Server response:", response_json)

        if response.status_code == 200 and response_json.get("status") == "success":
            # Extract encrypted OpenAI API key and IV
            encrypted_key_base64 = response_json.get("encrypted_key")
            iv_base64 = response_json.get("iv")

            if not encrypted_key_base64 or not iv_base64:
                update_connection_status(live_status=LIVE, verification_status=False)
                return False

            # Decrypt the OpenAI API key
            encryption_key = bytes.fromhex("000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f")
            encrypted_key = base64.b64decode(encrypted_key_base64)
            iv = base64.b64decode(iv_base64)
            cipher = AES.new(encryption_key, AES.MODE_CBC, iv)
            decrypted_key = cipher.decrypt(encrypted_key)

            # Validate padding
            padding_length = decrypted_key[-1]
            if padding_length < 1 or padding_length > 16:
                update_connection_status(live_status=LIVE, verification_status=False)
                return False
            decrypted_key = decrypted_key[:-padding_length].decode('utf-8').strip()

            # Set the OpenAI API key
            openai.api_key = decrypted_key

            # Update connection status
            update_connection_status(live_status=LIVE, verification_status=True)
            send_button.configure(state="normal")  # Enable the send button
            return True
        else:
            update_connection_status(live_status=LIVE, verification_status=False)
            return False

    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        update_connection_status(live_status=LIVE, verification_status=False)
        return False
    except Exception as e:
        print(f"Decryption error: {e}")
        update_connection_status(live_status=LIVE, verification_status=False)
        return False

def start_chat_session(UserID_5150):
    if LIVE:
        """
        Starts a chat session by generating a ChatSession_id and sending it to the server.

        Args:
            UserID_5150 (int): The user's ID.

        Returns:
            str: The ChatSession_id if successfully created, or None if failed.
        """
        session_payload = {
            "AccessKey_5150": AccessKey_5150,
            "ChatSession_id": chat_session_id,
            "user_id": UserID_5150
        }

        try:
            # Send the session start payload to the API
            response = requests.post("https://5150leagues.com/api/AllSight_Start_Session.php", data=session_payload)

            # Print raw response content for debugging
            print("Raw server response:", response.text)

            # Attempt to parse JSON response
            if response.status_code == 200:
                response_json = response.json()
                if response_json.get("status") == "success":
                    print(f"Session started successfully. ChatSession_id: {chat_session_id}")
                    return chat_session_id
                else:
                    print(f"Failed to start session: {response_json.get('message', 'No message provided')}")
            else:
                print(f"Server returned non-200 status code: {response.status_code}")
                print("Response content:", response.text)
            return None
        except requests.RequestException as e:
            print(f"Error connecting to the server: {e}")
            return None
        except json.JSONDecodeError:
            print("Failed to decode JSON response from the server.")
            return None
    else:
        print("OpenAI disabled: Skipping session start.")
        return None
        
# Call verify_access and display access denied message if necessary
if verify_access():
    chat_session_id = start_chat_session(UserID_5150)
    send_button.configure(state="normal")  # Enable the send button
else:
    send_button.configure(state="disabled")
 
def send_log_to_endpoint():
    if LIVE:
        if not chat_log:
            print("Chat log is empty. Skipping log submission.")
            return
        try:
            # Define the endpoint URL
            url = "https://5150leagues.com/api/save_chat_log.php"

            # Convert chat log to JSON format
            chat_log_json = json.dumps(chat_log)

            # Construct the payload with chat log and access key
            payload = {
                "user_id": UserID_5150,
                "AccessKey_5150": AccessKey_5150,  # Include Access Key for verification
                "chat_log": chat_log_json,
                "chat_session_id": chat_session_id,  # Include session ID for tracking
            }

            # Send the POST request with the chat log and access key
            response = requests.post(url, data=payload)

            # Print the raw response text for debugging
            print("Server response:", response.text)

            # Check if the request was successful
            if response.status_code == 200:
                response_json = response.json()
                if response_json.get("status") == "success":
                    print("Chat log successfully sent to the server.")
                else:
                    print(f"Failed to save chat log: {response_json.get('message', 'No message provided')}")
            else:
                print(f"Failed to send chat log. Status Code: {response.status_code}")
                print("Response:", response.text)

        except requests.RequestException as e:
            print(f"Error sending chat log to the server: {e}")
    else:
        print("OpenAI disabled: Skipping log submission.")

# Function to get a response from OpenAI API with streaming
def get_ai_response(prompt):
    global total_tokens_used
    if LIVE:
        try:
            response_text = ""
            response = openai.ChatCompletion.create(
                model=AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            # Collect message chunks and form the response
            for chunk in response:
                message_chunk = chunk['choices'][0]['delta'].get('content', '')
                if message_chunk:
                    response_text += message_chunk

            # Calculate tokens for AI response
            tokens_for_ai_response = calculate_tokens(response_text)
            total_tokens_used += tokens_for_ai_response

            return response_text
        except Exception as e:
            return "Error: " + str(e)
    else:
        # Mock response for testing
        time.sleep(2)  # Simulate delay
        print("OpenAI disabled: Using mock response.")
        if "100 word test" in prompt.lower():
            return (
                "Certainly! Here's a 100-word test: "
                "In the ever-changing landscape of technology, adaptability is key. "
                "Whether you're coding, analyzing data, or brainstorming innovative ideas, "
                "being open to learning and growth is essential. Python is a versatile "
                "programming language that empowers developers to build efficient and "
                "powerful applications. From AI to web development, the possibilities are "
                "endless. By exploring the nuances of Python, you can unlock a world of "
                "opportunities. So, embrace challenges and never stop experimenting. Success "
                "comes from persistence and curiosity!"
            )
        return "This is a test response to simulate OpenAI output."

# Function to fetch AI response in a separate thread
def fetch_response_in_background(user_input):
    response = get_ai_response(user_input)  # Get actual response from OpenAI API
    
    # Display the AI response in the main thread (UI updates should be in the main thread)
    root.after(0, lambda: display_message("AllSight", response))

# Function to handle user input and send message
def send_message(event=None):
    global total_tokens_used, chat_log

    user_input = entry.get()
    if user_input.strip() == "":
        return  # Don't send empty messages

    # Clean chat log before processing
    chat_log = clean_chat_log(chat_log)

    # Prevent duplicate user messages
    if chat_log and isinstance(chat_log[-1], dict):
        if chat_log[-1].get("sender") == "You" and chat_log[-1].get("message") == user_input:
            return  # Prevent duplicate user messages

    # Calculate tokens for user input
    tokens_for_user_input = calculate_tokens(user_input)
    total_tokens_used += tokens_for_user_input

    display_message("You", user_input)  # Display the user message
    chat_log.append({"sender": "You", "message": user_input})  # Add to chat log

    entry.delete(0, "end")  # Clear entry after sending

    # Start fetching AI response in a new thread
    threading.Thread(target=fetch_response_in_background, args=(user_input,), daemon=True).start()


def clean_chat_log(chat_log):
    """
    Ensures all chat log entries are dictionaries.
    Converts string entries to dictionary format if needed.
    """
    cleaned_log = []
    for entry in chat_log:
        if isinstance(entry, str):
            # Convert string entries into dictionary format
            if ": " in entry:
                sender, message = entry.split(": ", 1)
                cleaned_log.append({"sender": sender.strip(), "message": message.strip()})
            else:
                cleaned_log.append({"sender": "Unknown", "message": entry.strip()})
        elif isinstance(entry, dict):
            cleaned_log.append(entry)
    return cleaned_log

# Function to display messages in a single textbox
def display_message(sender=None, message=None, chat_log_data=None):
    global chat_log  # Ensure we're working with the global chat_log variable

    # Clear the chat_textbox if loading a saved session
    if chat_log_data:
        chat_textbox.configure(state="normal")
        chat_textbox.delete("1.0", "end")
        for entry in chat_log_data:
            # Format and insert each entry from the chat log
            chat_textbox.insert("end", entry + "\n\n")
        chat_textbox.configure(state="disabled")
        chat_textbox.see("end")
        return
    
    

    # Add new messages if sender and message are provided
    if sender and message:
        chat_textbox.configure(state="normal")
        formatted_message = f"{sender}: {message}\n\n"
        chat_textbox.insert("end", formatted_message)
        chat_log.append(f"{sender}: {message}")

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

        chat_textbox.configure(state="disabled")
        chat_textbox.see("end")

def report_to_support(report_type):
    def submit_report():
        issue_description = issue_textbox.get("1.0", "end").strip()
        if issue_description:
            # Convert chat log to JSON format
            chat_log_json = json.dumps(chat_log)
            payload = {
                "report_type": report_type,
                "description": issue_description,
                "chat_log": chat_log_json,
                "user_id": UserID_5150,
            }
            try:
                response = requests.post("https://5150leagues.com/api/AllSight_ReportChat.php", json=payload)
                if response.status_code == 200 and response.json().get("status") == "success":
                    tk.messagebox.showinfo("Success", "Report submitted successfully!")
                else:
                    tk.messagebox.showerror("Error", f"Failed to submit report: {response.text}")
            except Exception as e:
                tk.messagebox.showerror("Error", f"Error sending report: {e}")
            report_window.destroy()
        else:
            tk.messagebox.showerror("Error", "Report description cannot be empty!")

    # Create a new Toplevel window
    report_window = tk.Toplevel(root)
    report_window.title(f"Report {report_type.capitalize()}")
    report_window.geometry("400x450")  # Increased height to fit everything
    report_window.configure(bg="#1e1e1e")

    # Bring the report window to the front
    report_window.transient(root)  # Make the report window a child of the main window
    report_window.grab_set()       # Prevent interaction with the main window until the report is closed
    report_window.focus_force()    # Force focus on the report window

    # Add a label for the issue description
    ctk.CTkLabel(
        report_window, 
        text=f"Describe the {report_type} issue:", 
        fg_color="#1e1e1e",
        text_color="white",
        font=("Helvetica Neue", 12)
    ).pack(pady=10)

    # Add a Text widget for the issue description
    issue_textbox = tk.Text(
        report_window, 
        wrap="word", 
        bg="#333333", 
        fg="white", 
        font=("Helvetica Neue", 10),
        height=15
    )
    issue_textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # Add a modern CustomTkinter Submit button
    submit_button = ctk.CTkButton(
        report_window,
        text="Submit Report",
        fg_color="#007bff",  # Button background color
        hover_color="#0056b3",  # Button hover color
        text_color="white",
        font=("Helvetica Neue", 12),
        corner_radius=8,  # Rounded corners
        command=submit_report
    )
    submit_button.pack(side="bottom", pady=10)  # Positioned at the bottom

    # Ensure the report window stays in front
    report_window.lift()  # Lift the window to the top of the stacking order

def end_chat_session(chat_session_id, total_tokens, total_messages):
    if LIVE:
        """
        Ends a chat session by sending session details to the server.

        Args:
            chat_session_id (str): The unique session ID.
            total_tokens (int): Total tokens used during the session.
            total_messages (int): Total messages exchanged during the session.
        """
        end_session_payload = {
            "AccessKey_5150": AccessKey_5150,
            "ChatSession_id": chat_session_id,
            "total_tokens": total_tokens,
            "total_messages": total_messages
        }

        # Send the session end payload to the API
        response = requests.post("https://5150leagues.com/api/AllSight_End_Session.php", data=end_session_payload)

        if response.status_code == 200 and response.json().get("status") == "success":
            print("Session ended successfully.")
            return True
        else:
            print(f"Failed to end session: {response.text}")
            return False
    else:
        print("OpenAI disabled: Skipping session end.")
        return None

    """
    Update the Listbox with the last 10 chat logs.
    """
    chat_list.delete(0, 'end')  # Clear existing list entries
    print("Updating Chat Log List...")  # Debug message

    for log in chat_logs:
        chat_session_id = log['ChatSession_id']
        timestamp = log['timestamp']
        display_text = f"Session {chat_session_id} - {timestamp}"

        print("Adding to Listbox:", display_text)  # Debug each item being added

        # Add each log to the Listbox
        chat_list.insert('end', display_text)
        chat_sessions[chat_session_id] = log["chat_log"]  # Store logs in a dictionary for quick access

# Start the update check
update_in_background()

# Focus entry field on start
entry.focus_set()
entry.bind("<Return>", send_message)

# Add the function to send log when closing the application
def on_closing():
    """
    Triggered when the program is closed.
    Sends the session data and ends the session.
    """
    global total_tokens_used, chat_log, chat_session_id

    total_messages_sent = len(chat_log)  # Count the messages in the chat log

    # End the session
    if chat_session_id:
        end_chat_session(chat_session_id, total_tokens=total_tokens_used, total_messages=total_messages_sent)

    send_log_to_endpoint()  # Send log before closing
    root.destroy()

# Bind the close event
root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the main loop
root.mainloop()
