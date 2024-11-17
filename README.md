
<img src="./img/FreeGPT4_Banner(Nicoladipa).png" style="width:100%; max-width:500px; min-width:200px; aspect-ratio: 5/2"/>

[![Docker Image CI](https://github.com/aledipa/Free-GPT4-WEB-API/actions/workflows/docker-image.yml/badge.svg)](https://github.com/aledipa/Free-GPT4-WEB-API/actions/workflows/docker-image.yml)
[![GPT4-API-PyApp](https://github.com/aledipa/Free-GPT4-WEB-API/actions/workflows/python-app.yml/badge.svg)](https://github.com/aledipa/Free-GPT4-WEB-API/actions/workflows/python-app.yml)
![Docker Pulls](https://img.shields.io/docker/pulls/d0ckmg/free-gpt4-web-api)

<!-- <img src="https://status.freegpt4.ddns.net/getstatus" width="256" height="40" /> -->

# Free-GPT4-WEB-API

FreeGPT4-WEB-API is a python server that allows you to have a self-hosted GPT-4 Unlimited and Free WEB API, via the latest AI providers.

## Features
- Self-hosted GPT-4o API
- Unlimited usage
- Free of cost
- User-friendly GUI


## GUI Preview:

<!-- round angles images -->
<img src="./img/login.png" style="width:100%; max-width:500px; min-width:200px; aspect-ratio: 4/3" />
<img src="./img/settings.png" style="width:100%; max-width:500px; min-width:200px; aspect-ratio: 4/3" />

## Installation
1. Clone the repository: `git clone https://github.com/aledipa/Free-GPT4-WEB-API.git`
2. Navigate to the project directory: `cd Free-GPT4-WEB-API`
3. Install the required packages: `pip install -r requirements.txt`

## Requirements

- Python 3
- Flask[async]
- g4f (from [here](https://github.com/xtekky/gpt4free)).
- aiohttp
- aiohttp_socks
- auth
- Werkzeug

## Usage

_Note: It is recommended to [use the GUI](#to-use-the-web-gui)._

### Run the server 
Use the following command:
```shell
python3 FreeGPT4_Server.py [-h] [--remove-sources] [--enable-gui] 
                           [--private-mode] [--enable-history] [--password PASSWORD] 
                           [--cookie-file COOKIE_FILE] [--file-input] [--port PORT] 
                           [--model MODEL] [--provider PROVIDER] [--keyword KEYWORD] 
                           [--system-prompt SYSTEM_PROMPT] [--enable-proxies]
```


Options:

  `-h, --help`            show this help message and exit
  
  `--remove-sources`      Remove the sources from the response
  
  `--enable-gui`          Use a graphical interface for settings
  
  `--private-mode`        Use a private token to access the API
  
  `--enable-history`      Enable the history of the messages
  
  `--password PASSWORD`   Set or change the password for the settings page [mandatory in docker envirtonment]
  
  `--cookie-file COOKIE_FILE`
                        Use a cookie file
  
  `--file-input`          Add the file as input support
  
  `--port PORT`           Change the port (default: 5500)
  
  `--model MODEL`         Change the model (default: gpt-4)
  
  `--provider PROVIDER`   Change the provider (default: Bing)
  
  `--keyword KEYWORD`     Add the keyword support
  
  `--system-prompt SYSTEM_PROMPT`
                        Use a system prompt to 'customize' the answers
  
  `--enable-proxies`
                         Use one or more proxies to avoid being blocked or banned

### Make questions
Once the server is up and running, make sure that you're able to reach its address and type `?text=` followed by your question next to it.
You can replace ‘text’ with whatever you wish, either by using the `--keyword` flag or by changing the value of the ‘Input Keyword’ field on the Web GUI.

### Use the Web GUI
Once you've enabled it by running the server with the `--enable-gui` flag, just type `/settings` or `/login` next to the server's url

### Use it with Curl 
(credits to [@ayoubelmhamdi](https://github.com/ayoubelmhamdi)):

```shell
fileTMP="$1"
curl -s -F file=@"${fileTMP}" http://127.0.0.1:5500/
```


## Docker Installation
<img src="./img/docker-logo.webp" width="400" height="100" />

It's possible to install the docker image of this API by running this command:

`docker container run -v /path/to/your/cookies.json:/cookies.json:ro -p YOUR_PORT:5500 d0ckmg/free-gpt4-web-api`

just omit <code>-v /path/to/your/cookies.json:/cookies.json:ro</code> for using it without cookies

or alternatively, you can use a docker-compose file:

**docker-compose.yml**

```yaml
version: "3.9"
services:
  api:
    image: "d0ckmg/free-gpt4-web-api:latest"
    ports:
      - "YOUR_PORT:5500"
    #volumes:
    #  - /path/to/your/cookies.json:/cookies.json:ro
```

This will start the server and allow you to access the GPT-4 WEB API.

Once the server is running, you can access the API by sending HTTP requests to the server's address. The data for the requests should be sent via hotlinking and the response will be returned as plain text.

For example, to generate text using the API, you can send a GET request with the `text` parameter set to the text you want to use as a prompt and the (optional) `style` parameter set to the style you want to use. The default style is "balanced" and is recommended since it is faster. The generated text will be returned in the response as plain text.

To stop the server, you can press `CTRL+C` in the terminal where the server is running.
(credits to [@git-malik](https://github.com/git-malik))

## Siri Integration
<img src="./img/GPTMode_Logo.png" width="400" height="133" />

You can implement the power of GPT4 in Siri by using the [GPTMode Apple Shortcut](https://www.icloud.com/shortcuts/bfeed30555854958bd6165fa4d82e21b).
Then you can use it just by saying "GPT Mode" to Siri and then ask your question when prompted to do so.

## Configuration

The server can be configured by using the GUI or the corresponding parameters. The only cookie needed for the Bing model is _"_U"_.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=aledipa/Free-GPT4-WEB-API&type=Date)](https://star-history.com/#aledipa/Free-GPT4-WEB-API&Date)

## Notes

- The demo server may be overloaded and not always work as expected. (Check the "Demo Server Status" above)
- Any kind of contribution to the repository is welcome.

## Todo ✔️
- [x] Fix Demo Server
- [x] Update README
