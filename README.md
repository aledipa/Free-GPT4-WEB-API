<img src="./img/Free-GPT4-LOGO_(icon_by_vectorsmarket15).png" width="500" height="200" />

[![Docker Image CI](https://github.com/aledipa/Free-GPT4-WEB-API/actions/workflows/docker-image.yml/badge.svg)](https://github.com/aledipa/Free-GPT4-WEB-API/actions/workflows/docker-image.yml)
[![GPT4-API-PyApp](https://github.com/aledipa/Free-GPT4-WEB-API/actions/workflows/python-app.yml/badge.svg)](https://github.com/aledipa/Free-GPT4-WEB-API/actions/workflows/python-app.yml)

# Free-GPT4-WEB-API

FreeGPT4-WEB-API is a python server that allows you to have a self-hosted GPT-4 Unlimited and Free WEB API, via the latest Bing's AI.

## Requirements

- Python 3
- Flask
- `cookies.json` (optional, see [this guide](https://github.com/acheong08/EdgeGPT#getting-authentication-required) for its creation).
## Manual Installation
To install the required libraries, you can use the following command:

`pip3 install Flask`

### Usage

To run the server, use the following command:

(Logged with your account)
```shell
python3 FreeGPT4_Server.py --cookie-file /path/to/your/cookies.json
```
(Not logged)
```shell
python3 FreeGPT4_Server.py
```

If you want to use it with curl:

```shell
fileTMP="$1"
curl -s -F file=@"${fileTMP}" http://127.0.0.1:5500/
```
## Docker Installation
<img src="./img/docker-logo.webp" width="400" height="100" />

It's possible to install the docker image of this API by running this command:

`docker container run -v /path/to/your/cookies.json:/cookies.json:ro -p YOUR_PORT:5500 d0ckmg/free-gpt4-web-api`

or alternatively, you can use a docker-compose file:

**docker-compose.yml**

```yaml
version: "3.9"
services:
  api:
    image: "d0ckmg/free-gpt4-web-api:latest"
    ports:
      - "YOUR_PORT:5500"
    volumes:
      - /path/to/your/cookies.json:/cookies.json:ro
```

This will start the server and allow you to access the GPT-4 WEB API.

Once the server is running, you can access the API by sending HTTP requests to the server's address. The data for the requests should be sent via hotlinking and the response will be returned as plain text.

For example, to generate text using the API, you can send a GET request with the `text` parameter set to the text you want to use as a prompt and the (optional) `style` parameter set to the style you want to use. The default style is "balanced" and is recommended since it is faster. The generated text will be returned in the response as plain text.

To stop the server, you can press `CTRL+C` in the terminal where the server is running.

## Siri Integration
<img src="./img/GPTMode_Logo.png" width="400" height="133" />

You can implement the power of GPT4 in Siri by using the [GPTMode Apple Shortcut](https://www.icloud.com/shortcuts/bfeed30555854958bd6165fa4d82e21b).
Then you can use it just by saying "GPT Mode" to Siri and then ask your question when prompted to do so.

## Configuration

The server can be configured by editing the `FreeGPT4_Server.py` file. You can change the server's port, host, and other settings.

## Libraries

FreeGPT4-WEB-API uses the Flask and EdgeGPT libraries. Flask is a micro web framework for Python that allows you to easily create web applications. EdgeGPT is a library that provides an interface to the Bing's GPT-4, credits to [A. Cheong's EdgeGPT](https://github.com/acheong08/EdgeGPT).

## Notes

- The demo server may be overloaded and not always work as expected.
- Any kind of contribution to the repository is welcome.
