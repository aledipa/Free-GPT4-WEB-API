<img src="./img/Free-GPT4-LOGO_(icon_by_vectorsmarket15).png" width="800" height="200" />

# Free-GPT4-WEB-API

FreeGPT4-WEB-API is a python server that allows you to have a self-hosted GPT-4 Unlimited and Free WEB API, via the latest Bing's AI.

## Requirements

- Python 3
- Flask
- `cookies.json` (see [this guide](https://github.com/acheong08/EdgeGPT#getting-authentication-required) for its creation), this file is mandatory for the script to function.
## Manual Installation
To install the required libraries, you can use the following command:

`pip3 install Flask`

### Usage

To run the server, use the following command:

`python3 FreeGPT4_Server.py --cookie-file /path/to/your/cookies.json`
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

## Configuration

The server can be configured by editing the `FreeGPT4_Server.py` file. You can change the server's port, host, and other settings.

## Libraries

FreeGPT4-WEB-API uses the Flask and EdgeGPT libraries. Flask is a micro web framework for Python that allows you to easily create web applications. EdgeGPT is a library that provides an interface to the Bing's GPT-4, credits to [A. Cheong's EdgeGPT](https://github.com/acheong08/EdgeGPT).
