import re
import argparse
import json
import os

# GPT Library
import g4f

# Server
from flask import Flask, redirect, render_template
from flask import request
import getpass
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'data/'
# ALLOWED_EXTENSIONS = {'json'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000 # 16 MB

# Settings file path
SETTINGS_FILE = "./data/settings.json"

# Available providers
PROVIDERS = {
    "AItianhu": g4f.Provider.AItianhu,
    "Acytoo": g4f.Provider.Acytoo,
    "Aichat": g4f.Provider.Aichat,
    "Ails": g4f.Provider.Ails,
    "Bard": g4f.Provider.Bard,
    "Bing": g4f.Provider.Bing,
    "ChatgptAi": g4f.Provider.ChatgptAi,
    "ChatgptLogin": g4f.Provider.ChatgptLogin,
    "H2o": g4f.Provider.H2o,
    "HuggingChat": g4f.Provider.HuggingChat,
    "Opchatgpts": g4f.Provider.Opchatgpts,
    "OpenAssistant": g4f.Provider.OpenAssistant,
    "OpenaiChat": g4f.Provider.OpenaiChat,
    "Raycast": g4f.Provider.Raycast,
    "Theb": g4f.Provider.Theb,
    "Vercel": g4f.Provider.Vercel,
    "Wewordle": g4f.Provider.Wewordle,
    "You": g4f.Provider.You,
    "Yqcloud": g4f.Provider.Yqcloud,
}

def saveSettings(request, file):
    with open(file, "r") as f:
        data = json.load(f)
        f.close()
    with open(file, "w") as f:
        data["file_input"] = request.form["file_input"]
        data["remove_sources"] = request.form["remove_sources"]
        data["port"] = request.form["port"]
        # data["model"] = request.form["model"] #Considering to implement this
        data["keyword"] = request.form["keyword"]
        data["provider"] = request.form["provider"]
        file = request.files["cookie_file"]
        #checks if the file is not empty
        if file.filename != '':
            #checks if the file is a json file
            if file.filename.endswith('.json'):
                #saves the file
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                #updates the cookie_file
                data["cookie_file"] = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            else:
                print("The file is not a json file")

        json.dump(data, f)
        f.close()
    return

# Loads the settings from the file and updates the args
def applySettings(file):
    with open(file, "r") as f:
        data = json.load(f)
        args.keyword = data["keyword"]
        args.file_input = data["file_input"]
        args.port = data["port"]
        args.provider = data["provider"]
        args.model = data["model"]
        args.cookie_file = data["cookie_file"]
        args.remove_sources = data["remove_sources"]
        f.close()
    return

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
        question = request.args.get(args.keyword) #text
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
    print("COOKIES: " + str(len(args.cookie_file)))
    if (len(args.cookie_file) != 0):
        try:
            cookies = json.load(open(args.cookie_file)) # Loads the cookies from the file
            print("COOKIES: "+str(cookies))
            if (len(cookies) == 0):
                cookies = {"a": "b"} # Dummy cookies
        except Exception as error:
            print("[X] Error:", error)
            exit()
    else:
        cookies = {"a": "b"} # Dummy cookies
    # Set with provider
    response = (
        await PROVIDERS[args.provider].create_async(
            model=args.model,
            messages=[{"role": "user", "content": question,}],
            cookies=cookies,
            auth=True
        )
    )
    #Joins the response into a single string
    resp_str = ""
    for message in response:
        resp_str += message

    # Cleans the response from the resources links
    # INFO: Unsupported escape sequence in string literal
    if (str(args.remove_sources) == "True"):
        if re.search(r"\[\^[0-9]+\^\]\[[0-9]+\]", resp_str):
            resp_str = resp_str.split("\n\n")
            if len(resp_str) > 1:
                resp_str.pop(0)
            resp_str = re.sub(r"\[\^[0-9]+\^\]\[[0-9]+\]", "", str(resp_str[0]))
    # Returns the response
    return resp_str
    # return "<p id='response'>" + resp + "</p>" # Uncomment if preferred

def auth():
    if (data["password"] != ""):
        if (request.method == "POST"):
            password = request.form["password"]
            if (check_password_hash(data["password"], password)):
                return True
            else:
                return False
        else:
            return False
    else:
        return True

@app.route("/login", methods=["POST"])
async def login():
    if (auth()):
        try:
            providers=PROVIDERS
            data = json.loads(open(SETTINGS_FILE).read())
            return render_template("settings.html", **locals())
        except Exception as error:
            print("[X] Error:", error)
            return "Error: " + str(error)
    else:
        return render_template("login.html", **locals())

@app.route("/settings", methods=["GET", "POST"])
async def settings():
    if (args.enable_gui):
        return render_template("login.html", **locals())
    else:
        return "The GUI is disabled. In order to enable it, use the --enable-gui argument."

@app.route("/save", methods=["POST"])
async def save():
    if (auth()):
        try:
            if (request.method == "POST"):
                saveSettings(request, SETTINGS_FILE)
                applySettings(SETTINGS_FILE)
                
                return "New settings saved and applied successfully!"
            else:
                return render_template("login.html", **locals())
        except Exception as error:
            print("[X] Error:", error)
            return "Error: " + str(error)
    else:
        return render_template("login.html", **locals())

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
    parser.add_argument(
        "--enable-gui",
        action='store_true',
        required=False,
        help="needed if you want to use a graphical interface for settings",
    )
    parser.add_argument(
        "--password",
        action='store',
        required=False,
        help="optional, needed if you want to set a password for the settings page [mandatory in docker envirtonment]",
    )
    parser.add_argument(
        "--cookie-file",
        action='store',
        required=False,
        type=str,
        help="needed if you want to use a cookie file",
    )
    parser.add_argument(
        "--file-input",
        action='store_true',
        required=False,
        help="needed if you want to add the file as input support",
    )
    parser.add_argument(
        "--port",
        action='store',
        required=False,
        type=str,
        help="needed if you want to change the port (default: 5500)",
    )
    parser.add_argument(
        "--model",
        action='store',
        required=False,
        type=str,
        help="needed if you want to change the model (default: gpt_4)",
    )
    parser.add_argument(
        "--provider",
        action='store',
        required=False,
        type=str,
        help="needed if you want to change the provider (default: Bing)",
    )
    parser.add_argument(
        "--keyword",
        action='store',
        required=False,
        type=str,
        help="needed if you want to add the keyword support",
    )
    args = parser.parse_args()

    # Loads the settings from the file
    with open(SETTINGS_FILE, "r") as f:
        data = json.load(f)
        f.close()
    # Updates the settings
    with open(SETTINGS_FILE, "w") as f:
        if (args.keyword != None):
            data["keyword"] = args.keyword
        else:
            args.keyword = data["keyword"]

        if (args.file_input == False):
            args.file_input = data["file_input"]
        else:
            data["file_input"] = args.file_input

        if (args.port != None):
            data["port"] = args.port
        else:
            args.port = data["port"]

        if (args.provider != None):
            data["provider"] = args.provider
        else:
            args.provider = data["provider"]

        if (args.model != None):
            data["model"] = args.model
        else:
            args.model = data["model"]

        if (args.cookie_file != None):
            data["cookie_file"] = args.cookie_file
        else:
            args.cookie_file = data["cookie_file"]

        json.dump(data, f)
        f.close()


    if (args.enable_gui):
        #asks for password to set to lock the settings page
        #checks if settings.json contains a password
        if (data["password"] == ""):
            if(args.password != ""):
                password = args.password
                print("[V] Password set.")
                try:
                    data["password"] = password
                    with open(SETTINGS_FILE, "w") as f:
                        json.dump(data, f)
                        f.close()
                        print("[V] Password saved.") 
                except Exception as error:
                    print("[X] Error:", error)
                    exit()
            
            try:
                password = getpass.getpass("Settings page password:\n > ")
                confirm_password = getpass.getpass("Confirm password:\n > ")
                if(password == "" or confirm_password == ""):
                    print("[X] Password cannot be empty")
                    exit()
                if (password != confirm_password):
                    print("[X] Passwords don't match")
                    exit()
                else:
                    password = generate_password_hash(password)
                    confirm_password = generate_password_hash(confirm_password)
                    print("[V] Password set.")
                    try:
                        data["password"] = password
                        with open(SETTINGS_FILE, "w") as f:
                            json.dump(data, f)
                            f.close()
                            print("[V] Password saved.") 
                    except Exception as error:
                        print("[X] Error:", error)
                        exit()

            except Exception as error:
                print("[X] Error:", error)
                exit()
    else:
        print("[!] GUI disabled")

    #Starts the server, change the port if needed
    app.run("0.0.0.0", port=args.port, debug=False)
