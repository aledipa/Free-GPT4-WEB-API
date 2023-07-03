import json
import os
import re
import argparse

# GPT Library
import asyncio
from EdgeGPT.EdgeGPT import Chatbot, ConversationStyle
# Server
from flask import Flask
from flask import request


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
async def index() -> str:
    """
    Main function
    """
    # Starts the bot and gets the input and style
    print("Initializing...")
    bot = Chatbot(proxy=args.proxy)
    question = None
    style = "creative"

    print("start")
    if request.method == "GET":
        question = request.args.get("text")
        style = request.args.get('style')
        if (style != None and style in ["creative", "balanced", "precise"] and args.style == None):
            args.style = style
        print("get")
    else:
        file = request.files["file"]
        text = file.read().decode("utf-8")
        question = text
        print("Post reading the file", question)

    print("ici")
    if question is None:
        return "<p id='response'>Please enter a question</p>"
    print("\nInput: " + question)
    
    # Gets the response from the bot
    resp = (
            await bot.ask(
                prompt=question,
                conversation_style="creative",
                wss_link=args.wss_link,
                simplify_response=False
            )
        )
    
    try:
        resp = (resp["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"])[0]
    except:
        resp = resp["item"]["messages"][4]["text"]
    # Cleans the response from the resources links
    # INFO: Unsupported escape sequence in string literal
    if re.search("\[\^[0-9]+\^\]\[[0-9]+\]", resp):
        resp = resp.split("\n\n")
        if len(resp) > 1:
            resp.pop(0)
        resp = re.sub("\[\^[0-9]+\^\]\[[0-9]+\]", "", str(resp[0]))
    await bot.close()
    # Returns the response
    return resp
    # return "<p id='response'>" + resp + "</p>" # Uncomment if preferred


if __name__ == "__main__":
    print(
        """
        FreeGPT4 Web API - A Web API for GPT-4 (Using BingAI)
        Repo: github.com/aledipa/FreeGPT4-WEB-API
        By: Alessandro Di Pasquale

        EdgeGPT Credits: github.com/acheong08/EdgeGPT
    """,
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("--enter-once", action="store_true", default=True)
    parser.add_argument("--no-stream", action="store_true", default=True)
    parser.add_argument("--rich", action="store_true")
    parser.add_argument(
        "--proxy",
        help="Proxy URL (e.g. socks5://127.0.0.1:1080)",
        type=str,
    )
    parser.add_argument(
        "--wss-link",
        help="WSS URL(e.g. wss://sydney.bing.com/sydney/ChatHub)",
        type=str,
        default="wss://sydney.bing.com/sydney/ChatHub",
    )
    parser.add_argument(
        "--style",
        choices=["creative", "balanced", "precise"],
        default="balanced",
    )
    parser.add_argument(
        "--cookie-file",
        type=str,
        default="cookies.json",
        required=False,
        help="needed if environment variable COOKIE_FILE is not set",
    )
    args = parser.parse_args()
    if os.path.exists(args.cookie_file):
        os.environ["COOKIE_FILE"] = args.cookie_file
    else:
        print("[!] Warning: Cookie file not found, proceeding without cookies (no account mode).")
        #Creates dummy cookie file if not found
        with open("../cookies.json", 'w') as fp:
            fp.close()

    #Starts the server, change the port if needed
    app.run("0.0.0.0", port=5500, debug=False)
