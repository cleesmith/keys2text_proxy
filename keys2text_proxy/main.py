# HUGE NOTE: this app is meant to be used by one person along with novelcrafter!
# during dev/testing:
#   pip install -e .
#   python -m keys2text_proxy.main
# ...or do what users would do after pip install: 
#   keys2text_proxy
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
from contextlib import asynccontextmanager

from .api_mock       import chat_completion_stream as mock_chat_stream,       chat_completion_json as mock_chat_json
from .api_anthropic  import anthropic_models
from .api_anthropic  import chat_completion_stream as anthropic_chat_stream,  chat_completion_json as anthropic_chat_json
from .api_google     import google_models
from .api_google     import chat_completion_stream as gemini_chat_stream,     chat_completion_json as gemini_chat_json
from .api_groq       import groq_models
from .api_groq       import chat_completion_stream as groq_chat_stream,       chat_completion_json as groq_chat_json
from .api_openai     import openai_models
from .api_openai     import chat_completion_stream as openai_chat_stream,     chat_completion_json as openai_chat_json
from .api_openrouter import openrouter_models
from .api_openrouter import chat_completion_stream as openrouter_chat_stream, chat_completion_json as openrouter_chat_json
from .api_ollama     import ollama_models
from .api_ollama     import chat_completion_stream as ollama_chat_stream,     chat_completion_json as ollama_chat_json
from .api_lmstudio   import lmstudio_models
from .api_lmstudio   import chat_completion_stream as lmstudio_chat_stream,   chat_completion_json as lmstudio_chat_json
from .api_deepseek   import deepseek_models
from .api_deepseek   import chat_completion_stream as deepseek_chat_stream,   chat_completion_json as deepseek_chat_json

timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
CHAT_FILE = f"chat_{timestamp}.txt"

# nested dict to hold both stream and non_stream api handlers:
provider_to_api_handler = {
    "keys2text":        {"stream": mock_chat_stream,        "non_stream": mock_chat_json},
    "openai":           {"stream": openai_chat_stream,      "non_stream": openai_chat_json},
    "openrouter":       {"stream": openrouter_chat_stream,  "non_stream": openrouter_chat_json},
    "anthropic":        {"stream": anthropic_chat_stream,   "non_stream": anthropic_chat_json},
    "google":           {"stream": gemini_chat_stream,      "non_stream": gemini_chat_json},
    "groq":             {"stream": groq_chat_stream,        "non_stream": groq_chat_json},
    "lmstudio":         {"stream": lmstudio_chat_stream,    "non_stream": lmstudio_chat_json},
    "ollama":           {"stream": ollama_chat_stream,      "non_stream": ollama_chat_json},
    "deepseek":         {"stream": deepseek_chat_stream,    "non_stream": deepseek_chat_json},
}

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
        }
    ]
}

def append_models_to_all(models, provider):
    global all_models
    if not models:  # handle None or empty lists gracefully
        return
    for model_name in models:
        all_models["data"].append({
            "id": model_name,
            "object": "model",
            "created": datetime_to_timestamp(datetime.datetime.now()),
            "owned_by": provider
        })

@asynccontextmanager
async def lifespan(app: FastAPI):
    global all_models

    with open(CHAT_FILE, "a") as f:
        human_timestamp = datetime.datetime.now().strftime("%A, %b %d, %Y - %I:%M %p")
        f.write(f"Chat history for session starting at {human_timestamp}\n")
        full_path = os.path.abspath(f.name)

    print(f"\n***********************************************************")
    print(f"Welcome to Keys2Text Proxy to AI providers and chat models!")
    print(f". . . standby gathering a list of models based on your provider API keys:")
    for provider, handlers in provider_to_api_handler.items():
        models = None
        if provider == "anthropic":
            models = await anthropic_models()
        if provider == "google":
            models = await google_models()
        if provider == "groq":
            models = await groq_models()
        if provider == "openai":
            models = await openai_models()
        if provider == "ollama":
            models = await ollama_models()
        if provider == "lmstudio":
            models = await lmstudio_models()
        if provider == "openrouter":
            models = await openrouter_models()
        if provider == "deepseek":
            models = await deepseek_models()
        if models:
            append_models_to_all(models, provider)
    print(f"*** List of models available:\n{all_models}\n")
    print(f"Fire up novelcrafter and enjoy plain text files of your chats.")
    print(f"For this chat session see:")
    print(f"{full_path}")
    print(f"***********************************************************\n")

    # ready to handle proxy requests from novelcrafter or whatever:
    yield

    # now, after the yield, is the app shutting down, usually ctrl+c:
    print("* Note, if you see:")
    print("\tWARNING: All log messages before absl::InitializeLog() is called are written to STDERR")
    print("\tE0000 00:00:1735937246.100830 12394077 init.cc:229] grpc_wait_for_shutdown_with_timeout() timed out.")
    print("\t... or similar, these can safely be ignored.")
    print("Keys2Text Proxy is shutting down . . . goodbye!")


app = FastAPI(lifespan=lifespan) # deprecated: @app.on_event("startup")
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["*"], # dumb! so let's be more restrictive:
    allow_origins=["http://0.0.0.0:8000", "https://app.novelcrafter.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/v1/models")
async def list_models():
    return JSONResponse(content=all_models)


@app.post("/v1/chat/completions")
async def chat_completion(request: Request):
    # need Request as json to get the requested model and stream:
    request_dict = await request.json()

    model_requested = request_dict.get("model", "keys2text-mock")
    # find the 'owned_by' value (i.e. provider) for the given model name:
    provider = next((model["owned_by"] for model in all_models["data"] if model["id"] == model_requested), None)

    stream_requested = request_dict.get('stream', False)

    response_type = "stream" if stream_requested else "non_stream"
    default_handler = {"stream": mock_chat_stream, "non_stream": mock_chat_json}
    model_handler = provider_to_api_handler.get(provider, default_handler)[response_type]

    if stream_requested:
        return StreamingResponse(model_handler(request_dict, CHAT_FILE), media_type="text/event-stream")
    else:
        response_data = await model_handler(request_dict, CHAT_FILE)
        return JSONResponse(content=response_data)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run the keys2text_proxy FastAPI app.")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    args = parser.parse_args()
    uvicorn.run("keys2text_proxy.main:app", host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()

