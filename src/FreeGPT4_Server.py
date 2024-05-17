import re
import argparse
import json
import os
import random
import string
from uuid import uuid4

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

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000 # 16 MB

# Settings file path
SETTINGS_FILE = "./data/settings.json"
PROXIES_FILE = "./data/proxies.json"

# Available providers
PROVIDERS = {
    "Auto": "",
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
    "Bard": g4f.Provider.Bard,
    "DuckDuckGo": g4f.Provider.DuckDuckGo
}

GENERIC_MODELS = ["gpt-3.5-turbo", "gpt-4"]


print(
    """
    FreeGPT4 Web API - A Web API for GPT-4
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
    help="Remove the sources from the response",
)
parser.add_argument(
    "--enable-gui",
    action='store_true',
    required=False,
    help="Use a graphical interface for settings",
)
parser.add_argument(
    "--private-mode",
    action='store_true',
    required=False,
    help="Use a private token to access the API",
)
parser.add_argument(
    "--enable-proxies",
    action='store_true',
    required=False,
    help="Use one or more proxies to avoid being blocked or banned",
)
parser.add_argument(
    "--enable-history",
    action='store_true',
    required=False,
    help="Enable the history of the messages",
)
parser.add_argument(
    "--password",
    action='store',
    required=False,
    help="Optional, set a password for the settings page [mandatory in docker envirtonment]",
)
parser.add_argument(
    "--cookie-file",
    action='store',
    required=False,
    type=str,
    help="Use a cookie file",
)
parser.add_argument(
    "--file-input",
    action='store_true',
    required=False,
    help="Add the file as input support",
)
parser.add_argument(
    "--port",
    action='store',
    required=False,
    type=str,
    help="Change the port (default: 5500)",
)
parser.add_argument(
    "--model",
    action='store',
    required=False,
    type=str,
    help="Change the model (default: gpt_4)",
)
parser.add_argument(
    "--provider",
    action='store',
    required=False,
    type=str,
    help="Change the provider (default: Bing)",
)
parser.add_argument(
    "--keyword",
    action='store',
    required=False,
    type=str,
    help="Add the keyword support",
)
parser.add_argument(
    "--system-prompt",
    action='store',
    required=False,
    type=str,
    help="Use a system prompt to 'customize' the answers",
)

args, unknown = parser.parse_known_args()

# Get the absolute path of the script
script_path = os.path.abspath(__file__)
# Get the directory of the script
script_dir = os.path.dirname(script_path)
# Change the current working directory
os.chdir(script_dir)

# Loads the proxies from the file
if (args.enable_proxies and os.path.exists(PROXIES_FILE)):
    proxies = json.load(open(PROXIES_FILE))
else:
    proxies = None

# Loads the settings from the file
with open(SETTINGS_FILE, "r") as f:
    data = json.load(f)
    f.close()
# Updates the settings
with open(SETTINGS_FILE, "w") as f:
    if (args.keyword == None):
        args.keyword = data["keyword"]

    if (args.file_input == False):
        args.file_input = data["file_input"]

    if (args.enable_history == False):
        args.enable_history = data["message_history"]

    if (args.port == None):
        args.port = data["port"]

    if (args.provider == None):
        args.provider = data["provider"]

    if (args.model == None):
        args.model = data["model"]

    if (args.cookie_file == None):
        args.cookie_file = data["cookie_file"]

    if (args.system_prompt == None):
        args.system_prompt = data["system_prompt"]

    if (args.remove_sources == False):
        args.remove_sources = data["remove_sources"]

    if (args.private_mode and data["token"] == ""):
        token = str(uuid4())
        data["token"] = token
    elif (data["token"] != ""):
        token = data["token"]

    if (args.enable_proxies == False):
        args.enable_proxies = data["proxies"]

    json.dump(data, f)
    f.close()

message_history = [{"role": "system", "content": args.system_prompt}]

if (args.enable_gui):
    # Asks for password to set to lock the settings page
    # Checks if settings.json contains a password
    if (data["password"] == ""):
        try:
            if (args.password != None):
                password = args.password
                confirm_password = password
            else:
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

# Saves the settings to the file
def saveSettings(request, file):
    with open(file, "r") as f:
        data = json.load(f)
        f.close()
    with open(file, "w") as f:
        data["file_input"] = bool(request.form["file_input"] == "true")
        data["remove_sources"] = bool(request.form["remove_sources"] == "true")
        data["port"] = request.form["port"]
        data["model"] = request.form["model"]
        data["keyword"] = request.form["keyword"]
        data["provider"] = request.form["provider"]
        data["system_prompt"] = request.form["system_prompt"]
        data["message_history"] = bool(request.form["message_history"] == "true")
        data["proxies"] = bool(request.form["proxies"] == "true")
        file = request.files["cookie_file"]
        if (args.private_mode or bool(request.form["private_mode"] == "true")):
            data["token"] = request.form["token"]
        else:
            data["token"] = ""
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

        if (args.enable_proxies or data["proxies"]):
            # Extracts the proxies from the form
            # print("Proxies enabled")
            proxies = []
            i = 1
            while True:
                if (("proxy_" + str(i)) in request.form):
                    proxy = request.form["proxy_" + str(i)]
                    if (proxy != ""):
                        # Checks if the proxy syntax is correct
                        if (proxy.count(":") == 3 and proxy.count("@") == 1):
                            proxy = {
                                "protocol": proxy.split("://")[0],
                                "username": proxy.split("://")[1].split(":")[0],
                                "password": proxy.split("://")[1].split(":")[1].split("@")[0],
                                "ip": proxy.split("://")[1].split(":")[1].split("@")[1],
                                "port": proxy.split("://")[1].split(":")[2]
                            }
                            proxies.append(proxy)
                    i += 1
                else:
                    break

            # Saves the proxies to the file proxies.json
            with open(PROXIES_FILE, "w") as pf:
                json.dump(proxies, pf)
                pf.close()


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
        args.token = data["token"]
        args.remove_sources = data["remove_sources"]
        args.system_prompt = data["system_prompt"]
        args.enable_history = data["message_history"]
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
        if (args.private_mode and request.args.get("token") != data["token"]):
            return "<p id='response'>Invalid token</p>"
        print("get")
    else:
        file = request.files["file"]
        text = file.read().decode("utf-8")
        question = text
        print("Post reading the file", question)

    print("ici")
    if question is None:
        return "<p id='response'>Please enter a question</p>"

    # Gets the response from the bot
    # print(PROVIDERS[args.provider].params)  # supported args
    print("\nCookies: " + str(len(args.cookie_file)))
    print("\nInput: " + question)
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


    if (args.enable_history):
        print("History enabled")
        message_history.append({"role": "user", "content": question})
    else:
        print("History disabled")
        message_history.clear()
        message_history.append({"role": "system", "content": args.system_prompt})
        message_history.append({"role": "user", "content": question})

    proxy = None
    if (args.enable_proxies):
        # Extracts a proxy from the list
        proxy = random.choice(proxies)
        # Formats the proxy like https://user:password@host:port
        proxy = f"{proxy['protocol']}://{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}"
        print("Proxy: " + proxy)

    if (args.provider == "Auto"):
        response = (
            await g4f.ChatCompletion.create_async(
                model=args.model,
                messages=message_history,
                cookies=cookies,
                proxy=proxy
            )
        )
    else:
        response = (
            await g4f.ChatCompletion.create_async(
                model=args.model,
                provider=args.provider,
                messages=message_history,
                cookies=cookies,
                proxy=proxy
            )
        )

    print(response)

    #Joins the response into a single string
    resp_str = ""
    for message in response:
        resp_str += message

    # Cleans the response from the resources links
    if (args.remove_sources):
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

@app.route("/login", methods=["GET", "POST"])
async def login():
    if (args.enable_gui):
        return render_template("login.html", **locals())
    else:
        return "The GUI is disabled. In order to enable it, use the --enable-gui argument."

@app.route("/settings", methods=["GET", "POST"])
async def settings():
    if (request.method == "GET"):
        return redirect("/login", code=302)
    if (auth()):
        try:
            providers=PROVIDERS
            generic_models=GENERIC_MODELS
            data = json.loads(open(SETTINGS_FILE).read())
            proxies = json.loads(open(PROXIES_FILE).read())
            return render_template("settings.html", **locals())
        except Exception as error:
            print("[X] Error:", error)
            return "Error: " + str(error)
    else:
        return render_template("login.html", **locals())

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

@app.route("/models", methods=["GET"])
async def get_models():
    provider = request.args.get("provider")
    if (provider == "Auto"):
        return GENERIC_MODELS
    try:
        return PROVIDERS[provider].models
    except:
        return ["default"]

@app.route("/generatetoken", methods=["GET", "POST"])
async def get_token():
    return str(uuid4())

if __name__ == "__main__":
    # Starts the server, change the port if needed
    app.run("0.0.0.0", port=args.port, debug=False)
