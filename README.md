# 5150: AllSight Chat

AllSight Chat is a simple, customizable chat application powered by OpenAI’s GPT-4 model. Designed with Python and Tkinter, it features a sleek, dark-themed interface with message streaming for real-time conversational experience. AllSight is ideal for users looking to integrate AI-driven chat into desktop applications and for developers wanting to expand its functionality.

## Features
- **Real-Time AI Responses**: Uses OpenAI's GPT-4 model with streaming for a seamless conversation experience.
- **User-Friendly Interface**: Built with Tkinter, featuring color-coded message bubbles and a modern dark theme.
- **Simple Configuration**: Easily configurable with an OpenAI API key for quick setup.
- **Multi-User Ready**: Ready for collaborative development using Git version control.

## Getting Started

### Prerequisites
- **Python 3.7+**
- **OpenAI API Key**: Sign up at [OpenAI](https://openai.com/) and obtain an API key. (5150 LLC will provide it's key for early access.)

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/NinetyPear/AllSightChat.git
   cd AllSightChat

1. **Download Repository (Optional)**
   ```bash
   Download the Lasest Tag https://github.com/NinetyPear/AllSightChat/releases/tag/


2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt

3. **Set Up API Key**
   ```bash
   # config.py
   # REMOVE ".example" FROM THE FILENAME AFTER UPDATING THE API KEY TO config.py (Example filename: config.py | NOT config.example.py)
   OPENAI_API_KEY = "your-openai-api-key"
   AccessKey_5150 = "your-5150-access-key"
   UserID_5150 = "your-5150-userID"

4. **Run the Application**
   ```bash
   python chatbot.py
   or you can Run the .exe file named 'chat.exe'

### Usage
1) Enter your message in the input box and press "Send" or hit Enter.
2) Receive AI responses from AllSight in real-time, displayed in color-coded chat bubbles.
3) Customization Options: Modify bubble colors, text alignment, and more in the code to suit your preferences. (Work In Progress)

### Project Structure

```
AllSightChat/
│
├── config.py                 # Configuration file for API keys
├── chat.py                # Main application code
├── README.md                 # Project README
├── requirements.txt          # Python dependencies
├── .gitignore                # Ignored files in Git
│
└── ... 
```
### License
This project is licensed under the MIT License. See the LICENSE file for details.
