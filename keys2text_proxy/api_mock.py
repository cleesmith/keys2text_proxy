# api_mock.py
import os
import json
from fastapi import Request
from fastapi.responses import StreamingResponse, JSONResponse
from openai import OpenAI

mock_response = '''
I'm a figment of your imagination!\n
You have requested a model that is unknown.\n
Ensure the following is unchecked in your AI Connections:\n
  🔳 Use filenames instead of full path for models\n
... without the full path the provider becomes unknown.
Otherwise, check your settings and API keys; then try again.\n
You can do this! 😊
'''

async def chat_completion_json(request: Request, chat_file):
	# simulate a response for the JSON endpoint
	response_data = {
		"id": "mock1",
		"object": "chat.completion",
		"created": 1718313000,
		"model": "keys2text-mock",
		"choices": [
			{
				"index": 0,
				"message": {
					"role": "assistant",
					"content": mock_response
				},
				"finish_reason": "stop"
			}
		]
	}
	return response_data # i'm a dict

async def chat_completion_stream(request: Request, chat_file):
	print(f"\n$$$ mock_response={mock_response}\n")
	input_string = '''data: {"id":"chunk1","object":"chat.completion.chunk","created":1718313000,"model":"keys2text-mock","choices":[{"index":0,"delta":{"role":"assistant","content":"I'm a figment of your imagination!\\nYou have requested a model that is unknown.\\nEnsure the following is unchecked in your AI Connections:\\n   🔳 Use filenames instead of full path for models\\n... without the full path the provider becomes unknown.\\nOtherwise, check your settings and API keys; then try again.\\nYou can do this!  \\ud83d\\ude0a"},"finish_reason":null}]}'''
	json_part = input_string[len("data: "):]
	transformed_chunk = json.loads(json_part)
	yield f"data: {json.dumps(transformed_chunk)}\n\n".encode("utf-8")
	input_string = '''data: {"id":"chunk2","object":"chat.completion.chunk","created":1718313000,"model":"keys2text-mock","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}'''
	json_part = input_string[len("data: "):]
	transformed_chunk = json.loads(json_part)
	yield f"data: {json.dumps(transformed_chunk)}\n\n".encode("utf-8")
	yield b"data: [DONE]\n\n"

