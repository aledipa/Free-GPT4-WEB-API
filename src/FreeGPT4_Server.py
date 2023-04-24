import socket
import os
import re
# GPT Library
import EdgeGPT
# Server
from flask import Flask, request
app = Flask(__name__)

ADDRESS = socket.gethostbyname(socket.getfqdn())
#ADDRESS = "192.168.1.X" # Edit if needed, uncomment to use

@app.route('/')
async def index() -> None:
    """
    Main function
    """
    #Starts the bot and gets the input and style
    print("Initializing...")
    bot = EdgeGPT.Chatbot(proxy=args.proxy)
    question = request.args.get('text')
    if (question == None):
        return "<p id='response'>Please enter a question</p>"
    style = request.args.get('style')
    if (style != None and style in ["creative", "balanced", "precise"] and args.style == None):
        args.style = style
        print("\nStyle: " + style)
    print("\nInput: " + question)
    #Gets the response from the bot
    resp = (
        (
            await bot.ask(
                prompt=question,
                conversation_style=args.style,
                wss_link=args.wss_link,
            )
        )["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"],
    )[0]
    #Cleans the response from the resources links
    if (re.search("\[\^[0-9]+\^\]\[[0-9]+\]", resp)):
        resp = resp.split("\n\n")
        if (len(resp) > 1):
            resp.pop(0)
        resp = re.sub("\[\^[0-9]+\^\]\[[0-9]+\]", "", str(resp[0]))
    await bot.close()
    #Returns the response
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
    parser = EdgeGPT.argparse.ArgumentParser()
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
        parser.print_help()
        parser.exit(
            1,
            "ERROR: use --cookie-file or set environemnt variable COOKIE_FILE",
        )

    #Starts the server, change the port if needed
    app.run(host=ADDRESS, port=5005, debug=False)