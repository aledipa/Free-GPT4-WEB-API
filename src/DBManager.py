import os
import sqlite3
import secrets
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash

# Database file path
DATABASE_FILE = "./data/settings.db"

# Connect to the SQLite database
def connect(file):
    conn = sqlite3.connect(file)
    return conn, conn.cursor()

# Define your classes
class DBM:
    def __init__(self):
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)

    def reset_settings(self):
        # Connect to the SQLite database
        conn, cursor = connect(DATABASE_FILE)

        # Create the settings table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id SERIAL PRIMARY KEY,
            keyword TEXT,
            file_input BOOLEAN,
            port TEXT,
            provider TEXT,
            model TEXT,
            cookie_file TEXT,
            token TEXT,
            remove_sources BOOLEAN,
            system_prompt TEXT,
            message_history BOOLEAN,
            proxies BOOLEAN,
            password TEXT,
            fast_api BOOLEAN,
            virtual_users BOOLEAN,
            chat_history TEXT
        )
        ''')

        # Pre-configured settings data
        preconfigured_settings = (
            1,  # ID
            "text",  # keyword
            True,  # file_input
            "5500",  # port
            "Auto",  # provider
            "gpt-4",  # model
            "data/cookies.json",  # cookie_file
            # str(uuid4()),  # pre-made token
            "",  # token
            True,  # remove_sources
            "",  # system_prompt
            False,  # message_history
            False,  # proxies
            "",  # password
            False, # fast_api
            False, # virtual_users
            ""  # chat_history
        )

        # Insert the pre-configured settings into the settings table
        cursor.execute('''
        INSERT OR REPLACE INTO settings (
            id, keyword, file_input, port, provider, model, cookie_file, token, remove_sources, system_prompt, message_history, proxies, password, fast_api, virtual_users, chat_history
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', preconfigured_settings)

        # Commit the changes and close the connection
        conn.commit()
        conn.close()
        print("[v] Pre-configured settings have been saved to settings.db")

    def add_user(self, username, password="autogen"):
        if (username.lower() == "admin"):
            print("[X] Error adding User: \"admin\" is not a valid username.")
            return
        # Connect to the SQLite database
        conn, cursor = connect(DATABASE_FILE)
        if (password == "autogen" or len(password) == 0):
            password = generate_password_hash(username)
        else:
            password = generate_password_hash(password)

        #Create the user's personal settings
        # remove_sources BOOLEAN,
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS personal (
            token TEXT PRIMARY KEY,
            provider TEXT,
            model TEXT,
            system_prompt TEXT,
            message_history BOOLEAN,
            username TEXT UNIQUE,
            password TEXT,
            chat_history TEXT
        )
        ''')

        # New Pre-configured user data
        preconfigured_user = (
            str(uuid4()),  # TOKEN ID
            "Auto",  # provider
            "gpt-4",  # model
            "",  # system_prompt
            False,  # message_history
            username, # username
            password,  # password (hashed)
            ""  # chat_history
        )

        try:
            # Insert the new pre-configured user into the personal table
            cursor.execute('''
            INSERT INTO personal (
                token, provider, model, system_prompt, message_history, username, password, chat_history
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', preconfigured_user)

            # Commit the changes and close the connection
            conn.commit()
            conn.close()
            print("[v] Pre-configured New User '{0}' has been added to settings.db".format(username))
        except Exception as e:
            conn.close()
            print("[X] Error adding User: {0}".format(e))

    def add_user_by_token(self, token, username, password="autogen"):
        # Connect to the SQLite database
        conn, cursor = connect(DATABASE_FILE)
        if (password == "autogen" or len(password) == 0):
            password = generate_password_hash(username)
        else:
            password = generate_password_hash(password)

        #Create the user's personal settings
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS personal (
            token TEXT PRIMARY KEY,
            provider TEXT,
            model TEXT,
            system_prompt TEXT,
            message_history BOOLEAN,
            username TEXT UNIQUE,
            password TEXT,
            chat_history TEXT
        )
        ''')

        # New Pre-configured user data
        preconfigured_user = (
            token,  # TOKEN ID
            "Auto",  # provider
            "gpt-4",  # model
            "",  # system_prompt
            False,  # message_history
            username, # username
            password,  # password (hashed)
            ""  # chat_history
        )

        try:
            # Insert the new pre-configured user into the personal table
            cursor.execute('''
            INSERT INTO personal (
                token, provider, model, system_prompt, message_history, username, password, chat_history
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', preconfigured_user)

            # Commit the changes and close the connection
            conn.commit()
            conn.close()
            print("[v] Pre-configured New User '{0}' has been added to settings.db".format(username))
        except Exception as e:
            conn.close()
            print("[X] Error adding User: {0}".format(e))

    def delete_user_by_token(self, token):
        conn, cursor = connect(DATABASE_FILE)
        
        try:
            cursor.execute('''
            DELETE FROM personal WHERE token = ?
            ''', (token,))
            
            conn.commit()
            conn.close()
            print("[v] User with token '{0}' has been successfully removed.".format(token))
        except Exception as e:
            conn.close()
            print("[X] Error removing User: {0}".format(e))

    def delete_user_by_name(self, username):
        conn, cursor = connect(DATABASE_FILE)
        
        try:
            cursor.execute('''
            DELETE FROM personal WHERE username = ?
            ''', (username,))
            
            conn.commit()
            conn.close()
            print("[v] User with username '{0}' has been successfully removed.".format(username))
        except Exception as e:
            conn.close()
            print("[X] Error removing User: {0}".format(e))

    def rename_user(self, old_username, new_username):
        conn, cursor = connect(DATABASE_FILE)

        try:
            cursor.execute('''
            UPDATE personal SET username = ? WHERE username = ?
            ''', (new_username, old_username))

            conn.commit()
            conn.close()
            print("[v] User '{0}' has been renamed to '{1}'.".format(old_username, new_username))
        except Exception as e:
            conn.close()
            print("[X] Error renaming User: {0}".format(e))

    def rename_user_by_token(self, token, new_username):
        conn, cursor = connect(DATABASE_FILE)

        try:
            cursor.execute('''
            UPDATE personal SET username = ? WHERE token = ?
            ''', (new_username, token))

            conn.commit()
            conn.close()
            print("[v] User with token '{0}' has been renamed to '{1}'.".format(token, new_username))
        except Exception as e:
            conn.close()
            print("[X] Error renaming User: {0}".format(e))

    def save_admin_chat_history(self, chat_history):
        conn, cursor = connect(DATABASE_FILE)

        try:
            cursor.execute('''
            UPDATE settings SET chat_history = ?
            ''', (chat_history,))

            conn.commit()
            conn.close()
            print("[v] Admin chat history saved.")
        except Exception as e:
            conn.close()
            print("[X] Error saving admin chat history: {0}".format(e))

    def save_user_chat_history(self, username, chat_history):
        if (username == "admin"):
            self.save_admin_chat_history(chat_history)
            return
        conn, cursor = connect(DATABASE_FILE)

        try:
            cursor.execute('''
            UPDATE personal SET chat_history = ? WHERE username = ?
            ''', (chat_history, username))
            conn.commit()
            conn.close()
            print("[v] User chat history saved.")
        except Exception as e:  
            conn.close()
            print("[X] Error saving user chat history: {0}".format(e))
            
    def get_user_chat_history(self, username):
        conn, cursor = connect(DATABASE_FILE)

        try:
            cursor.execute('''
            SELECT chat_history FROM personal WHERE username = ?
            ''', (username,))

            conn.commit()
            chat_history = cursor.fetchone()
            conn.close()
            print("[v] User chat history returned.")
            return chat_history[0] if chat_history else None
        except Exception as e:
            conn.close()
            print("[X] Error reading user chat history: {0}".format(e))

    def get_user_system_prompt(self, username):
        conn, cursor = connect(DATABASE_FILE)

        try:
            cursor.execute('''
            SELECT system_prompt FROM personal WHERE username = ?
            ''', (username,))

            conn.commit()
            system_prompt = cursor.fetchone()
            conn.close()
            print("[v] User system prompt returned.")
            return system_prompt[0] if system_prompt else None
        except Exception as e:
            conn.close()
            print("[X] Error reading user system prompt: {0}".format(e))

    def get_admin_chat_history(self):
        conn, cursor = connect(DATABASE_FILE)

        try:
            cursor.execute('''
            SELECT chat_history FROM settings
            ''')

            conn.commit()
            chat_history = cursor.fetchone()
            conn.close()
            print("[v] Admin chat history returned.")
            return chat_history[0] if chat_history else None
        except Exception as e:
            conn.close()
            print("[X] Error reading admin chat history: {0}".format(e))

    def get_admin_system_prompt(self):
        conn, cursor = connect(DATABASE_FILE)

        try:
            cursor.execute('''
            SELECT system_prompt FROM settings
            ''')

            conn.commit()
            system_prompt = cursor.fetchone()
            conn.close()
            print("[v] Admin system prompt returned.")
            return system_prompt[0] if system_prompt else None
        except Exception as e:
            conn.close()
            print("[X] Error reading admin system prompt: {0}".format(e))

    def get_users(self):
        conn, cursor = connect(DATABASE_FILE)

        try:
            cursor.execute('''
            SELECT username FROM personal
            ''')

            conn.commit()
            users = cursor.fetchall()
            conn.close()
            print("[v] All usernames returned.")
            return [item[0] for item in users]
        except Exception as e:
            conn.close()
            print("[X] Error reading usernames: {0}".format(e))

    def get_tokens(self):
        conn, cursor = connect(DATABASE_FILE)

        try:
            cursor.execute('''
            SELECT token FROM personal
            ''')

            conn.commit()
            tokens = cursor.fetchall()
            conn.close()
            print("[v] All tokens returned.")
            return [item[0] for item in tokens]
        except Exception as e:
            conn.close()
            print("[X] Error reading tokens: {0}".format(e))

    def get_user_settings(self, username):
        conn, cursor = connect(DATABASE_FILE)

        try:
            cursor.execute('''
            SELECT * FROM personal WHERE username = ?
            ''', (username,))

            conn.commit()
            user_settings = cursor.fetchall()
            conn.close()
            user_settings = {
                "token": user_settings[0][0],
                "provider": user_settings[0][1],
                "model": user_settings[0][2],
                "system_prompt": user_settings[0][3],
                "message_history": user_settings[0][4],
                "username": user_settings[0][5],
                "password": user_settings[0][6],
                "chat_history": user_settings[0][7]
            }
            print("[v] User settings returned.")
            print("User settings: {0}".format(user_settings))
            return user_settings
        except Exception as e:
            conn.close()
            print("[X] Error reading user settings: {0}".format(e))
    
    def get_all_users_settings(self):
        conn, cursor = connect(DATABASE_FILE)

        try:
            cursor.execute('''
            SELECT * FROM personal
            ''')

            conn.commit()
            users_settings = cursor.fetchall()
            conn.close()
            users_settings_list = []
            for user in users_settings:
                user_settings = {
                    "token": user[0],
                    "provider": user[1],
                    "model": user[2],
                    "system_prompt": user[3],
                    "message_history": user[4],
                    "username": user[5],
                    "password": user[6],
                    "chat_history": user[7]
                }
                users_settings_list.append(user_settings)
            print("[v] All users settings returned.")
            return users_settings_list
        except Exception as e:
            conn.close()
            print("[X] Error reading all users settings: {0}".format(e))

    def get_username_by_token(self, token):
        conn, cursor = connect(DATABASE_FILE)

        try:
            cursor.execute('''
            SELECT username FROM personal WHERE token = ?
            ''', (token,))

            conn.commit()
            username = cursor.fetchone()

            # If the username is not found, checks in the settings table to see if it is an admin user
            if username is None:
                cursor.execute('''
                SELECT id FROM settings WHERE token = ?
                ''', (token,))
                conn.commit()
                username = cursor.fetchone()
                if username is not None:
                    username = ("admin",)
            else:
                username = username[0]
            
            conn.close()
            print("[v] Username for token '{0}' returned: {1}".format(token, username))
            return username
        except Exception as e:
            conn.close()
            print("[X] Error reading username: {0}".format(e))

# Block to test the library when run as a script
if __name__ == "__main__":
    # Test functions and classes here
    print("Testing DBManager...")
    obj = DBM()