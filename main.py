import os
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocketDisconnect
from utils import stream_response

from memgpt_api import MemGptAPI

from schemas import Session, Message

load_dotenv()

app = FastAPI()


origins = [
    os.getenv("FRONT_URI", "http://localhost:8000"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

####################################################################################
# This SECTION IS JUST FOR TESTING PURPOSES

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MemGPT Chat</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
        }

        h1, h2 {
            color: #333;
        }

        .container {
            max-width: 500px;
            width: 100%;
            background-color: #fff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
            transition: opacity 0.5s ease-in-out;
        }

        #step1, #step2 {
            opacity: 1;
            padding: 20px;
        }

        #step2 {
            display: none;
        }

        form {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 10px;
        }

        #messages {
            max-height: 300px;
            overflow-y: auto;
            padding: 10px;
            display: flex;
            flex-direction: column-reverse;
        }

        input[type="text"] {
            padding: 8px;
            margin: 5px;
            border: 1px solid #ccc;
            border-radius: 4px;
            flex-grow: 1;
        }

        input[type="submit"] {
            padding: 8px;
            margin: 5px;
            cursor: pointer;
            background-color: #333;
            color: #fff;
            border: none;
            border-radius: 4px;
        }

        .messages-container {
            max-height: 300px;
            overflow-y: auto;
            padding: 10px;
            display: flex; 
            flex-direction: row; 
        }

        .message {
            margin: 5px;
            border-radius: 8px;
            max-width: 70%;
            overflow-wrap: break-word;
        }

        .user-message {
            background-color: #4CAF50;
            color: #fff;
            align-self: flex-end;
            text-align: right;
        }

        .bot-message {
            background-color: #008CBA;
            color: #fff;
            align-self: flex-start;
            text-align: left;
        }
    </style>
</head>
<body>
    <h1>MemGPT Chats API Test</h1>

    <div class="container" id="step1">
        <form onsubmit="initSession(event)" style="display: flex; flex-direction: row;">
            <h2> 
                Initiate and connect a Session: <input type="submit" value="Init Session" />
            </h2>
        </form>
        <span id="initMessage" class="init-message"></span>
        <form onsubmit="connectSession(event)" style="display: flex; flex-direction: row;">
            <h2>
                Session ID: <input type="text" id="session_id" value="" />
            </h2>
            <input type="submit" value="Connect Session" /> <span id="State"></span>
        </form>
    </div>

    <div class="container" id="step2">
        <h2 style="text-align: center"> Chat </h2>
        <div id="messages" class="messages-container"></div>
        <form onsubmit="sendMessage(event)" style="display: flex; flex-direction: row;">
            <input type="text" name="message" placeholder="Type your message..." style="flex-grow: 1; margin-right: 5px;" />
            <input type="submit" value="Send" style="margin-top: 5px;" />
        </form>
    </div>

    <script>
        function initSession(event) {
            fetch('http://localhost:8000/chat/init')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('session_id').value = data.session;
                    var initMessage = document.getElementById('initMessage');
                    initMessage.innerHTML = 'Session initialized. Connect below.';
                    initMessage.style.color = 'red';
                    document.getElementById('State').innerHTML = '';
                });

            event.preventDefault();
        }

        var ws = null;
        function connectSession(event) {
            var session_id = document.getElementById('session_id').value;
            ws = new WebSocket('ws://localhost:8000/chat/socket/' + session_id);
            ws.onopen = function(event) {
                document.getElementById('State').innerHTML = 'Connected. Start chatting below.';
                document.getElementById('step1').style.opacity = '0';
                document.getElementById('step2').style.display = 'block';
                setTimeout(() => {
                    document.getElementById('step1').style.display = 'none';
                    document.getElementById('step2').style.opacity = '1';
                }, 500);
            };
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages');
                var message = document.createElement('p');
                var content = document.createTextNode(event.data);
                message.appendChild(content);
                messages.appendChild(message);
            };
            event.preventDefault();
        }

        function sendMessage(event) {
            var input = document.querySelector('input[name="message"]');
            ws.send(input.value);
            input.value = '';
            event.preventDefault();
        }
    </script>
</body>
</html>
"""

@app.get("/")
async def root():
    return HTMLResponse(HTML)

#################################################################################

@app.get("/chat/init", response_model=Session)
async def init():
    """
    Init chat session

    :return: Session ID
    """
    return Session(session=str(uuid.uuid4()))


@app.websocket("/chat/socket/{session_id}")
async def socket_chat(websocket: WebSocket, session_id: str):
    """
    Chat websocket endpoint

    :param session_id: Session ID for agent
    """
    try:
        memgpt_api = MemGptAPI(session_id)

        await websocket.accept()
        try:
            while True:
                prompt = await websocket.receive_text()
                print("Waiting for api response......")

                message = memgpt_api.send_message(prompt)
                await websocket.send_text(message)
        except WebSocketDisconnect:
            print("Client disconnected")

    except Exception as err:
        print(err)
        await websocket.close()


@app.post("/chat/stream/{session_id}", response_class=StreamingResponse)
async def streaming_chat(session_id: str, message: Message):
    """
    Chat streaming endpoint

    :param session_id: Session ID for agent
    """
    memgpt_api = MemGptAPI(session_id)
    message = memgpt_api.send_message(message.prompt)

    return StreamingResponse(stream_response(message), media_type="text/event-stream")
