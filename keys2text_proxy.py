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


def datetime_to_timestamp(date):
    # convert a datetime object to a Unix timestamp
    return int(time.mktime(date.timetuple()))

all_models = {
    "object": "list",
    "data": [
        {
            "id": "keys2text-mock",
            "object": "model",
            "created": datetime_to_timestamp(datetime.datetime(2025, 1, 1)),
            "owned_by": "keys2text"
        },
        {
            "id": "claude-3-5-sonnet-20240620",
            "object": "model",
            "created": datetime_to_timestamp(datetime.datetime(2024, 6, 20)),
            "owned_by": "anthropic"
        },
        {
            "id": "gpt-3.5-turbo",
            "object": "model",
            "created": datetime_to_timestamp(datetime.datetime(2022, 1, 1)),
            "owned_by": "openai"
        },
        {
            "id": "gemini-1.5-pro",
            "object": "model",
            "created": datetime_to_timestamp(datetime.datetime(2023, 12, 31)),
            "owned_by": "google"
        },
        {
            "id": "llama3-70b-8192",
            "object": "model",
            "created": datetime_to_timestamp(datetime.datetime(2023, 12, 31)),
            "owned_by": "groq"
        },
        {
            "id": "lmstudio",
            "object": "model",
            "created": datetime_to_timestamp(datetime.datetime(2023, 12, 31)),
            "owned_by": "lmstudio"
        },
        {
            "id": "tinyllama",
            "object": "model",
            "created": datetime_to_timestamp(datetime.datetime(2023, 12, 31)),
            "owned_by": "ollama"
        }
    ]
}


@app.get("/v1/models")
async def list_models():
    return JSONResponse(content=all_models)

@app.post("/v1/chat/completions")
async def chat_completion(request: Request):
    # need Request as json to get the requested model and stream:
    request_dict = await request.json()

    model_requested = request_dict.get("model", "keys2text-mock")
    # find the 'owned_by' value (provider) for the given model name:
    provider = next((model["owned_by"] for model in all_models["data"] if model["id"] == model_requested), None)

    stream_requested = request_dict.get('stream', False)

    # a nested dict to hold both stream and non_stream api handlers:
    provider_to_api_handler = {
        "keys2text":        {"stream": mock_chat_stream,      "non_stream": mock_chat_json},
        "openai":           {"stream": openai_chat_stream,    "non_stream": openai_chat_json},
        "anthropic":        {"stream": anthropic_chat_stream, "non_stream": anthropic_chat_json},
        "google":           {"stream": gemini_chat_stream,    "non_stream": gemini_chat_json},
        "groq":             {"stream": groq_chat_stream,      "non_stream": groq_chat_json},
        "lmstudio":         {"stream": lmstudio_chat_stream,  "non_stream": lmstudio_chat_json},
        "ollama":           {"stream": ollama_chat_stream,    "non_stream": ollama_chat_json},
    }

    response_type = "stream" if stream_requested else "non_stream"
    default_handler = {"stream": mock_chat_stream, "non_stream": mock_chat_json}
    model_handler = provider_to_api_handler.get(provider, default_handler)[response_type]

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

