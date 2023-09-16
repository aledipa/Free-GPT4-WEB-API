import re
import argparse

# GPT Library
import g4f

# Server
from flask import Flask
from flask import request


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
async def index() -> str:
    """
    Main function
    """
    # Starts the bot and gets the input
    print("Initializing...")
    question = None

    print("start")
    if request.method == "GET":
        question = request.args.get("text")
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
    print(g4f.Provider.Bing.params)  # supported args
    # Set with provider
    response = (
        await g4f.Provider.Bing.create_async(
            model="gpt-4",
            # provider=g4f.Provider.Bing,
            messages=[{"role": "user", "content": question,}],
            cookies={"a": "b"},
            auth=True
        )
    )
    #Joins the response into a single string
    resp_str = ""
    for message in response:
        resp_str += message

    # Cleans the response from the resources links
    # INFO: Unsupported escape sequence in string literal
    if (args.remove_sources):
        if re.search("\[\^[0-9]+\^\]\[[0-9]+\]", resp_str):
            resp_str = resp_str.split("\n\n")
            if len(resp_str) > 1:
                resp_str.pop(0)
            resp_str = re.sub("\[\^[0-9]+\^\]\[[0-9]+\]", "", str(resp_str[0]))
    # Returns the response
    return resp_str
    # return "<p id='response'>" + resp + "</p>" # Uncomment if preferred


if __name__ == "__main__":
    print(
        """
        FreeGPT4 Web API - A Web API for GPT-4 (Using BingAI)
        Repo: github.com/aledipa/FreeGPT4-WEB-API
        By: Alessandro Di Pasquale

        GPT4Free Credits: github.com/xtekky/gpt4free
    """,
    )
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--remove-sources",
        action='store_true',
        required=False,
        help="needed if you want to remove the sources from the response",
    )
    args = parser.parse_args()

    #Starts the server, change the port if needed
    app.run("0.0.0.0", port=5500, debug=False)
