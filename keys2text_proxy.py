# python -B keys2text_proxy.py
import os
import signal
import sys
import time
import datetime
import json
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import uvicorn

from api_mock       import chat_completion_stream as mock_chat_stream,      chat_completion_json as mock_chat_json
from api_anthropic  import chat_completion_stream as anthropic_chat_stream, chat_completion_json as anthropic_chat_json
from api_google     import google_models
from api_google     import chat_completion_stream as gemini_chat_stream,    chat_completion_json as gemini_chat_json
from api_groq       import chat_completion_stream as groq_chat_stream,      chat_completion_json as groq_chat_json
from api_openai     import chat_completion_stream as openai_chat_stream,    chat_completion_json as openai_chat_json
from api_ollama     import chat_completion_stream as ollama_chat_stream,    chat_completion_json as ollama_chat_json
from api_lmstudio   import chat_completion_stream as lmstudio_chat_stream,  chat_completion_json as lmstudio_chat_json

timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
CHAT_FILE = f"chat_{timestamp}.txt"

def signal_handler(sig, frame):
    # define a signal handler to handle SIGINT ctrl-c in terminal
    print("Exiting...\n")
    sys.exit(0)

# register the signal handler for SIGINT
signal.signal(signal.SIGINT, signal_handler)

# app = FastAPI(debug=True) # no debug for prod
app = FastAPI()

# configure CORS
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["*"], # bad! so be more restrictive:
    allow_origins=["http://0.0.0.0:8000", "https://app.novelcrafter.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/v1/models")
def list_models():

    def datetime_to_timestamp(date):
        # convert a datetime object to a Unix timestamp
        return int(time.mktime(date.timetuple()))

    models = {
        "object": "list",
        "data": [
            {
                "id": "claude-3-5-sonnet-20240620",
                "object": "model",
                "created": datetime_to_timestamp(datetime.datetime(2024, 6, 20)),
                "owned_by": "Anthropic"
            },
            {
                "id": "claude-3-haiku-20240307",
                "object": "model",
                "created": datetime_to_timestamp(datetime.datetime(2024, 3, 7)),
                "owned_by": "Anthropic"
            },
            {
                "id": "claude-3-sonnet-20240229",
                "object": "model",
                "created": datetime_to_timestamp(datetime.datetime(2024, 2, 29)),
                "owned_by": "Anthropic"
            },
            {
                "id": "claude-3-opus-20240229",
                "object": "model",
                "created": datetime_to_timestamp(datetime.datetime(2024, 2, 29)),
                "owned_by": "Anthropic"
            },
            {
                "id": "gpt-3.5-turbo",
                "object": "model",
                "created": datetime_to_timestamp(datetime.datetime(2022, 1, 1)),
                "owned_by": "OpenAI"
            },
            {
                "id": "llama3-70b-8192",
                "object": "model",
                "created": datetime_to_timestamp(datetime.datetime(2023, 12, 31)),
                "owned_by": "Meta/Groq"
            },
            {
                "id": "gemini-1.5-pro",
                "object": "model",
                "created": datetime_to_timestamp(datetime.datetime(2023, 12, 31)),
                "owned_by": "Google"
            },
            {
                "id": "lmstudio",
                "object": "model",
                "created": datetime_to_timestamp(datetime.datetime(2023, 12, 31)),
                "owned_by": "LM Studio"
            },
            {
                "id": "tinyllama",
                "object": "model",
                "created": datetime_to_timestamp(datetime.datetime(2023, 12, 31)),
                "owned_by": "Ollama"
            },
            {
                "id": "api-keys2text-mock",
                "object": "model",
                "created": datetime_to_timestamp(datetime.datetime(2024, 6, 15)),
                "owned_by": "Keys2Text"
            }
        ]
    }
    return JSONResponse(content=models)


@app.post("/v1/chat/completions")
async def chat_completion(request: Request):
    # print("\nRequest:")
    # print(f"Method: {request.method}")
    # print(f"URL: {request.url}")
    # print(f"Headers: {request.headers}")
    # # print(f"Body: {await request.body()}")
    # print("-------------------------------")

    # need Request as json to get the requested model and stream:
    request_dict = await request.json()

    model_requested = request_dict.get("model", "api-keys2text-mock")
    stream_requested = request_dict.get('stream', False)

    # a nested dictionary/dict to hold both stream and non_stream functions
    model_to_module = {
        "keys2text-mock":             {"stream": mock_chat_stream,      "non_stream": mock_chat_json},
        "gpt-3.5-turbo":              {"stream": openai_chat_stream,    "non_stream": openai_chat_json},
        "claude-3-haiku-20240307":    {"stream": anthropic_chat_stream, "non_stream": anthropic_chat_json},
        "claude-3-sonnet-20240229":   {"stream": anthropic_chat_stream, "non_stream": anthropic_chat_json},
        "claude-3-opus-20240229":     {"stream": anthropic_chat_stream, "non_stream": anthropic_chat_json},
        "claude-3-5-sonnet-20240620": {"stream": anthropic_chat_stream, "non_stream": anthropic_chat_json},
        "llama3-70b-8192":            {"stream": groq_chat_stream,      "non_stream": groq_chat_json},
        "gemini-1.5-pro":             {"stream": gemini_chat_stream,    "non_stream": gemini_chat_json},
        "lmstudio":                   {"stream": lmstudio_chat_stream,  "non_stream": lmstudio_chat_json},
        "tinyllama":                  {"stream": ollama_chat_stream,    "non_stream": ollama_chat_json},
    }

    response_type = "stream" if stream_requested else "non_stream"
    # use the default mock_chat_stream if model_name is not found in the dictionary:
    default_handler = {"stream": mock_chat_stream, "non_stream": mock_chat_json}
    model_handler = model_to_module.get(model_requested, default_handler)[response_type]

    # print(f"POST: /v1/chat/completions in chat_completion:\nmodel_requested={model_requested}\nstream_requested={stream_requested}\nresponse_type={response_type}\nmodel_handler={model_handler}\n***************\n")
    # print(f"**************************\ngoogle models:\n{await google_models()}\n**************************\n")

    if stream_requested:
        return StreamingResponse(model_handler(request_dict, CHAT_FILE), media_type="text/event-stream")
    else:
        response_data = await model_handler(request_dict, CHAT_FILE)
        return JSONResponse(content=response_data)


if __name__ == "__main__":
    with open(CHAT_FILE, "a") as f:
        human_timestamp = datetime.datetime.now().strftime("%A, %b %d, %Y - %I:%M %p")
        f.write(f"Chat history for session starting at {human_timestamp}\n")

    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)

