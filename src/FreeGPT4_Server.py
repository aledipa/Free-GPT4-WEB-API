import re
import argparse
import json
import os
import random
import string
import sqlite3
from uuid import uuid4
import threading

# GPT Library
import g4f
from g4f.api import run_api

# Server
from flask import Flask, redirect, render_template
from flask import request
import getpass
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from DBManager import DBM



app = Flask(__name__)

UPLOAD_FOLDER = 'data/'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000 # 16 MB

# Settings file path
SETTINGS_FILE = "./data/settings.db"
PROXIES_FILE = "./data/proxies.json"

# Available providers
PROVIDERS = {
    "Auto": "",
    "BlackBox": g4f.Provider.Blackbox,
    "DeepInfraChat": g4f.Provider.DeepInfraChat,
    "HuggingChat": g4f.Provider.HuggingChat,
    "OpenaiChat": g4f.Provider.OpenaiChat,
    "Wewordle": g4f.Provider.WeWordle,
    "You": g4f.Provider.You,
    "Yqcloud": g4f.Provider.Yqcloud,
    "HuggingChat": g4f.Provider.HuggingChat,
    "HuggingFace": g4f.Provider.HuggingFace
    
}

GENERIC_MODELS = ["gpt-4", "gpt-4o", "gpt-4o-mini"]


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
    help="Set or change the password for the settings page [mandatory in docker envirtonment]",
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
parser.add_argument(
    "--enable-fast-api",
    action='store_true',
    required=False,
    help="Use the fast API standard (PORT 1337 - compatible with OpenAI integrations)",
)
parser.add_argument(
    "--enable-virtual-users",
    action='store_true',
    required=False,
    help="Giives the chance to create and manage new users",
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

# Crates the Fast API Thread
t = threading.Thread(target=run_api,name="fastapi")

# Loads the settings from the file
def load_settings(file=SETTINGS_FILE):
    conn = sqlite3.connect(file)
    c = conn.cursor()
    c.execute("SELECT * FROM settings")
    data = c.fetchone()
    conn.close()
    # Converts the data to a dictionary
    data = {
        "keyword": data[1],
        "file_input": data[2],
        "port": data[3],
        "provider": data[4],
        "model": data[5],
        "cookie_file": data[6],
        "token": data[7],
        "remove_sources": data[8],
        "system_prompt": data[9],
        "message_history": data[10],
        "proxies": data[11],
        "password": data[12],
        "fast_api": data[13],
        "virtual_users": data[14]
    }
    print(data)
    return data

def start_fast_api():
    print("[!] FAST API PORT: 1336")
    t.daemon = True
    t.start()

# Updates the settings
data = load_settings()
if (args.keyword == None):
    args.keyword = data["keyword"]

if (args.file_input == False):
    args.file_input = data["file_input"]

if (args.port == None):
    args.port = data["port"]

if (args.provider == None):
    args.provider = data["provider"]

if (args.model == None):
    args.model = data["model"]

if (args.cookie_file == None):
    args.cookie_file = data["cookie_file"]

if (args.private_mode and data["token"] == ""):
    token = str(uuid4())
    data["token"] = token
elif (data["token"] != ""):
    token = data["token"]
    args.private_mode = True

if (args.remove_sources == False):
    args.remove_sources = data["remove_sources"]

if (args.system_prompt == None):
    args.system_prompt = data["system_prompt"]

if (args.enable_history == False):
    args.enable_history = data["message_history"]

if (args.enable_proxies == False):
    args.enable_proxies = data["proxies"]

if (args.enable_fast_api or data["fast_api"]):
    start_fast_api()


if (args.enable_gui):
    try:
        set_password = True
        if (args.password != None):
            password = args.password
            confirm_password = password
        else:
            if (data["password"] == ""):
                password = getpass.getpass("Settings page password:\n > ")
                confirm_password = getpass.getpass("Confirm password:\n > ")
            else:
                set_password = False

        if (set_password):
            if(password == "" or confirm_password == ""):
                print("[X] Password cannot be empty")
                exit()

            if ((password != confirm_password) and (data["password"] == "")):
                print("[X] Passwords don't match")
                exit()
            else:
                password = generate_password_hash(password)
                confirm_password = generate_password_hash(confirm_password)
                print("[V] Password set.")
                try:
                    conn = sqlite3.connect(SETTINGS_FILE)
                    c = conn.cursor()
                    c.execute("UPDATE settings SET password = ?", (password,))
                    conn.commit()
                    conn.close()
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
def save_settings(request, file):
    conn = sqlite3.connect(file)
    c = conn.cursor()
    c.execute("UPDATE settings SET file_input = ?", (bool(request.form["file_input"] == "true"),))
    c.execute("UPDATE settings SET remove_sources = ?", (bool(request.form["remove_sources"] == "true"),))
    c.execute("UPDATE settings SET port = ?", (request.form["port"],))
    c.execute("UPDATE settings SET model = ?", (request.form["model"],))
    c.execute("UPDATE settings SET keyword = ?", (request.form["keyword"],))
    c.execute("UPDATE settings SET provider = ?", (request.form["provider"],))
    c.execute("UPDATE settings SET system_prompt = ?", (request.form["system_prompt"],))
    c.execute("UPDATE settings SET message_history = ?", (bool(request.form["message_history"] == "true"),))
    c.execute("UPDATE settings SET proxies = ?", (bool(request.form["proxies"] == "true"),))
    c.execute("UPDATE settings SET fast_api = ?", (bool(request.form["fast_api"] == "true"),))
    c.execute("UPDATE settings SET virtual_users = ?", (bool(request.form["virtual_users"] == "true"),))
    if (len(request.form["new_password"]) > 0):
        c.execute("UPDATE settings SET password = ?", (generate_password_hash(request.form["new_password"]),))

    file = request.files["cookie_file"]
    if (bool(request.form["private_mode"] == "true")):
        c.execute("UPDATE settings SET token = ?", (request.form["token"],))
        args.private_mode = True
    else:
        c.execute("UPDATE settings SET token = ''")
        args.private_mode = False
    #checks if the file is not empty
    if file.filename != '':
        #checks if the file is a json file
        if file.filename.endswith('.json'):
            #saves the file
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            #updates the cookie_file
            c.execute("UPDATE settings SET cookie_file = ?", (os.path.join(app.config['UPLOAD_FOLDER'], filename),))
        else:
            print("The file is not a json file")

    if (args.enable_proxies or bool(request.form["proxies"] == "true")):
        # Extracts the proxies from the form
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

    if (bool(request.form["fast_api"] == "true") and not args.enable_fast_api):
        start_fast_api()

    conn.commit()
    conn.close()

    if (bool(request.form["virtual_users"] == "true")):
        dbm = DBM()
        old_tokens = dbm.get_tokens()
        new_users = []
        print(str(request.form))
        # the user's key is 'username_<tokenvalue>' (with the literal word "username", the real username is stored in the value), extract the token value from the key and associate it with the co[...]
        new_tokens = [key.split("_")[1] for key in request.form.keys() if key.startswith('username_')]
        new_users = [value for key, value in request.form.items() if key.startswith('username_')]
        # combine the two lists into a dictionary
        new_users = dict(zip(new_tokens, new_users))

        # adds the new users to the database
        for token in new_users:
            if (token not in old_tokens):
                dbm.add_user_by_token(token, new_users[token])
        
        # updates the users in the database (new usernames) with dbm.rename_user_by_token
        for token in new_users:
            if (token in old_tokens):
                dbm.rename_user_by_token(token, new_users[token])

        # removes the old users from the database
        removed_users = list(set(old_tokens) - set(new_users))

        for user_to_delete in removed_users:
            dbm.delete_user_by_token(user_to_delete)

    return

def save_user_settings(request, file, username):
    print("Saving user settings for: " + username)
    conn = sqlite3.connect(file)
    c = conn.cursor()

    c.execute("UPDATE personal SET provider = ? WHERE username = ?", (request.form["provider"], username))
    c.execute("UPDATE personal SET model = ? WHERE username = ?", (request.form["model"], username))
    c.execute("UPDATE personal SET system_prompt = ? WHERE username = ?", (request.form["system_prompt"], username))
    c.execute("UPDATE personal SET message_history = ? WHERE username = ?", (bool(request.form["message_history"] == "true"), username))
    
    conn.commit()
    conn.close()

    if (request.form["new_password"] != ""):
        password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]
        if (password == "" or confirm_password == ""):
            print("[X] Password cannot be empty")
            exit()

        if ((password != confirm_password)):
            print("[X] Passwords don't match")
            exit()
        else:
            password = generate_password_hash(password)
            print("[V] Password set.")
            try:
                conn = sqlite3.connect(SETTINGS_FILE)
                c = conn.cursor()
                c.execute("UPDATE personal SET password = ? WHERE username = ?", (password, username))
                conn.commit()
                conn.close()
                print("[V] Password saved.")
            except Exception as error:
                print("[X] Error:", error)
                exit()
    return

# Loads the settings from the file and updates the args
def apply_settings(file):
    data = load_settings(file)
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
    args.enable_proxies = data["proxies"]
    args.password = data["password"]
    args.enable_fast_api = data["fast_api"]
    args.enable_virtual_users = data["virtual_users"]
    return


@app.route("/", methods=["GET", "POST"])
async def index() -> str:
    """
    Main function
    """

    # Starts the bot and gets the input
    print("Initializing...")
    question = None
    model = args.model
    provider = args.provider
    system_prompt = args.system_prompt
    user = "admin"
    chat_history = [{"role": "system", "content": system_prompt}]  # Initializes the chat history

    print("start")
    if request.method == "GET":
        question = request.args.get(args.keyword) #text
        print(args.private_mode)
        if (args.private_mode and request.args.get("token") != data["token"]):
            return "<p id='response'>Invalid token</p>"
        print("Virtual users: " + str(args.enable_virtual_users))
        if (args.enable_virtual_users):
            token = request.args.get("token")
            if (token != None):
                # Checks if the token is valid
                dbm = DBM()
                user = dbm.get_username_by_token(token)
                if (user == None):
                    return "<p id='response'>Invalid token</p>"
                elif (user == "admin"):
                    print("Admin user")
                    # Initializes the message history
                    if (args.enable_history):
                        # Loads the message history from the database
                        chat_history = json.loads(dbm.get_admin_chat_history())
                    chat_history.append({"role": "user", "content": question})
                    chat_history.insert(0, {"role": "system", "content": system_prompt})
                else:
                    print("Virtual user: " + user)
                        
                    # Loads the user settings
                    user_settings = dbm.get_user_settings(user)
                    model = user_settings["model"]
                    provider = user_settings["provider"]
                    system_prompt = user_settings["system_prompt"]
                    message_history = user_settings["message_history"]
                    print("User settings loaded: " + str(user_settings))

                    if (message_history):
                        if (len(dbm.get_user_chat_history(user)) == 0):
                            chat_history = [{"role": "system", "content": system_prompt}]
                        else:
                            chat_history = json.loads(dbm.get_user_chat_history(user))
                    chat_history.append({"role": "user", "content": question})
                    chat_history.insert(0, {"role": "system", "content": system_prompt})
        else:
            if (args.enable_history):
                print("[i] History enabled")
                dbm = DBM()
                if (len(dbm.get_admin_chat_history()) == 0):
                    chat_history = [{"role": "system", "content": system_prompt}]
                else:
                    chat_history = json.loads(dbm.get_admin_chat_history())
                chat_history.append({"role": "user", "content": question})
            else:
                print("[i] History disabled")
                chat_history.clear()
                chat_history.append({"role": "system", "content": system_prompt})
                chat_history.append({"role": "user", "content": question})
        
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
                model=model,
                messages=chat_history,
                cookies=cookies,
                proxy=proxy
            )
        )
    else:
        response = (
            await g4f.ChatCompletion.create_async(
                model=model,
                provider=provider,
                messages=chat_history,
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

    if (args.enable_history):
        chat_history.append({"role": "assistant", "content": resp_str})
    # Saves the chat history to the database
    if (args.enable_virtual_users):
        # dbm = DBM()
        if (user == "admin"):
            if (args.enable_history):
                dbm.save_admin_chat_history(json.dumps(chat_history))
        else:
            message_history = dbm.get_user_settings(user)["message_history"]
            if (message_history):
                dbm.save_user_chat_history(user, json.dumps(chat_history))

    # Returns the response
    return resp_str
    # return "<p id='response'>" + resp + "</p>" # Uncomment if preferred

def auth():
    # Reads the password from the data file
    data = load_settings()
    # Checks if the password is set
    if (data["password"] != ""):
        if (request.method == "POST"):
            username = request.form["username"]
            if (username != "admin"):
                return False
            password = request.form["password"]
            if (check_password_hash(data["password"], password)):
                return True
            else:
                return False
        else:
            return False
    else:
        return True

def user_auth():
    if (args.enable_virtual_users):
        # Reads the password from the data file
        dbm = DBM()
        data = dbm.get_all_users_settings()
        # Checks if the password is set
        if (request.method == "POST"):
            username = request.form["username"]
            password = request.form["password"]
            for user in data:
                if (user["username"] == username and check_password_hash(user["password"], password)):
                    return True
            return False
        else:
            return False
    else:
        return True

@app.route("/login", methods=["GET", "POST"])
async def login():
    if (args.enable_gui):
        virtual_users = args.enable_virtual_users
        return render_template("login.html", **locals())
    else:
        return "The GUI is disabled. In order to enable it, use the --enable-gui argument."

@app.route("/settings", methods=["GET", "POST"])
async def settings():
    virtual_users = args.enable_virtual_users
    if (request.method == "GET"):
        return redirect("/login", code=302)
    if (auth()):
        try:
            username = "admin"
            providers=PROVIDERS
            generic_models=GENERIC_MODELS
            data = load_settings()
            proxies = json.loads(open(PROXIES_FILE).read())
            if (args.enable_virtual_users):
                dbm = DBM()
                users_data = dbm.get_all_users_settings()
            return render_template("settings.html", **locals())
        except Exception as error:
            print("[X] Error:", error)
            return "Error: " + str(error)
    elif (user_auth()):
        try:
            username = request.form["username"]
            if (args.enable_virtual_users):
                providers=PROVIDERS
                generic_models=GENERIC_MODELS
                dbm = DBM()
                data = dbm.get_user_settings(username)
                print(data)   
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
                save_settings(request, SETTINGS_FILE)
                apply_settings(SETTINGS_FILE)

                return "New settings saved and applied successfully!"
            else:
                return render_template("login.html", **locals())
        except Exception as error:
            print("[X] Error:", error)
            return "Error: " + str(error)
    else:
        return render_template("login.html", **locals())
    
@app.route("/save/<username>", methods=["POST"])
def save_user(username):
    if (user_auth()):
        try:
            if (request.method == "POST"):
                save_user_settings(request, SETTINGS_FILE, username)

                return "New settings saved and applied successfully!"
            else:
                return render_template("login.html", **locals())
        except Exception as error:
            print("[X] Error:", error)
            return "Error: " + str(error)
    else:
        virtual_users = args.enable_virtual_users
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
def get_token():
    return str(uuid4())

if __name__ == "__main__":
    # Starts the server, change the port if needed
    app.run("0.0.0.0", port=args.port, debug=False)