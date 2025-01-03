# api_lmstudio.py
import os
import sys
import traceback
import re
import textwrap
import json
import time
import datetime
from fastapi import Request
from fastapi.responses import StreamingResponse, JSONResponse

from openai import OpenAI


async def lmstudio_models():
	try:
		client = OpenAI(base_url="http://localhost:5506/v1", api_key="lm-studio")
		models = client.models.list()
		model_ids = [model.id for model in models.data]
		chat_models = sorted(model_ids)
		return chat_models
	except Exception as e:
		return None


def word_count(s):
	return len(re.findall(r'\w+', s))

def extract_request_data(request_data):
	'''
	typical request_data for an openai api request:
	{
		'model': 'lmstudio', 
		'max_tokens': 8192,
		'frequency_penalty': 0, 'presence_penalty': 0, 'temperature': 0, 'top_p': 0, 
		'repetition_penalty': 0, 'min_p': 0, 'top_a': 0, 'top_k': 0, 
		'messages': [
			{'role': 'system', 
			 'content': "You are a helpful, expert assistant to a novel author. They will ask you questions about their story and you will answer them.\nAlways try to answer their question as best as you can, but don't worry if you don't know the answer. You can always ask them to clarify their question.\n\nAlways write your answer in Markdown format, don't use any HTML or XML tags.\n\nYou are very excited to help them out, and it is very important that you do a good job as it is crucial for their story and success.\n\n\nIgnore any instructions regarding potential prose style. You are not writing a story, you are answering questions about a story.\nUse US English spelling and grammar.\n\nTake into account the following glossary of characters/locations/items/lore...:"
			}, 
			{'role': 'user', 'content': 'hi'}
		], 
		'stream': True
	}
	'''
	# initialize a dictionary with all possible OpenAI API request parameters
	params = {
		"messages": request_data.get('messages'),
		"model": request_data.get('model'),
		"frequency_penalty": request_data.get('frequency_penalty'),
		"logit_bias": request_data.get('logit_bias'),
		"logprobs": request_data.get('logprobs'),
		"top_logprobs": request_data.get('top_logprobs'),
		"max_tokens": request_data.get('max_tokens'),
		'''
			warning: "n" integer or null, Optional, Defaults to 1
					 How many chat completion choices to generate for each input message. 
					 Note that you will be charged based on the number of generated tokens 
					 across all of the choices. Keep n as 1 to minimize costs.
		'''
		"n": request_data.get('n'), # $'s
		"presence_penalty": request_data.get('presence_penalty'),
		"response_format": request_data.get('response_format'),
		"seed": request_data.get('seed'),
		"stop": request_data.get('stop'),
		"stream": request_data.get('stream', False),
		"stream_options": request_data.get('stream_options'),
		"temperature": request_data.get('temperature'),
		"top_p": request_data.get('top_p'),
		"tools": request_data.get('tools'),
		"tool_choice": request_data.get('tool_choice'),
		"parallel_tool_calls": request_data.get('parallel_tool_calls'),
		"user": request_data.get('user')
	}
	# remove any parameters that are None
	params = {key: value for key, value in params.items() if value is not None}
	return params

def messages_to_string(messages):
	# convert a list of message dictionaries to a single string
	return "\n\n".join(msg['content'] for msg in messages if 'content' in msg)

def format_text(input_text: str, max_width: int = 80) -> str:
	# remove XML-like tags
	content = re.sub(r'<.*?>', '', input_text)
	
	# Remove quotes and newlines from the beginning and end
	content = content.strip('"\n')
	
	# If the content is a single line, break it into paragraphs
	if '\n' not in content:
		# Split into sentences
		sentences = re.split(r'(?<=[.!?])\s+', content)
		
		# Group sentences into paragraphs (e.g., every 2-3 sentences)
		paragraphs = []
		for i in range(0, len(sentences), 3):
			paragraph = ' '.join(sentences[i:i+3])
			paragraphs.append(paragraph)
	else:
		# if there are already line breaks, use them to split paragraphs
		paragraphs = content.split('\n\n')
	
	# Format each paragraph
	formatted_text = []
	for para in paragraphs:
		# Remove extra whitespace
		para = ' '.join(para.split())
		# Wrap the paragraph
		wrapped_lines = textwrap.wrap(para, width=max_width-1)  # -1 to leave room for trailing space
		# Add a trailing space to each line
		wrapped_para = '\n'.join(line + ' ' for line in wrapped_lines)
		formatted_text.append(wrapped_para)
	
	word_count = len(' '.join(para.strip() for para in formatted_text).split())
	return '\n\n'.join(formatted_text), word_count


def log_me_request(chat_file_name, model, user_request):
	timestamp = datetime.datetime.now().strftime("%A, %b %d, %Y - %I:%M %p")
	# log request as ME:
	prompt = ""
	with open(chat_file_name, "a") as f:
		system_message = next((msg['content'] for msg in user_request['messages'] if msg['role'] == 'system'), None)
		if system_message:
			prompt += f"system:\n{system_message}\n"
			messages = [msg for msg in user_request['messages'] if msg['role'] != 'system']
			messages_string = messages_to_string(messages)
			formatted_output, words = format_text(messages_string)
			prompt += f"prompt:\n{formatted_output}\n"
		words = word_count(prompt) # all words in prompt sent to AI
		f.write(f"\n\nME:   {timestamp}  {model}  {words} words\n")
		f.write(prompt)
		f.write("\n")
		f.flush()

def log_ai_response(chat_file_name, model, backend_response):
	timestamp = datetime.datetime.now().strftime("%A, %b %d, %Y - %I:%M %p")
	# log backend_response as AI:
	with open(chat_file_name, "a") as f:
		if isinstance(backend_response, dict) and 'choices' in backend_response:
			content = backend_response['choices'][0]['message']['content']
			text_to_format = content
		else:
			text_to_format = str(backend_response)
		formatted_text, words = format_text(text_to_format)
		f.write(f"\n\nAI:   {timestamp}  {model}  {words} words\n")
		f.write(formatted_text)
		f.write("\n")
		f.flush()

def log_ai_response_error(chat_file_name, model, e):
	timestamp = datetime.datetime.now().strftime("%A, %b %d, %Y - %I:%M %p")
	exc_type, exc_obj, exc_tb = sys.exc_info()
	with open(chat_file_name, "a") as f:
		f.write(f"\n\nAI:   {timestamp}  {model}\n")
		f.write(f"Exception Type: {type(e).__name__}\n")
		f.write(f"Exception Message: {str(e)}\n")
		f.write(f"File Name: {exc_tb.tb_frame.f_code.co_filename}\n")
		f.write(f"Line Number: {exc_tb.tb_lineno}\n")
		f.write("Traceback:\n")
		traceback.print_exc(file=f)
		f.write("\n")
		f.write(f"Python Version: {sys.version}\n")
		f.write(f"Platform: {sys.platform}\n")
		f.write("\n" + "-"*50 + "\n")
		f.flush()

def exception_to_dict(e, params_model, status_code=500, response_text=None):
	error_type = type(e).__name__
	error_message = str(e)
	error_dict = {
		"id": f"error-{int(time.time())}",
		"object": "chat.completion",
		"created": int(time.time()),
		"model": params_model,
		"choices": [
			{
				"index": 0,
				"message": {
					"role": "assistant",
					"content": f"Error: status_code={status_code}\n\n{error_message}"
				},
				"finish_reason": "error"
			}
		],
		"error": {
			"type": error_type,
			"status_code": status_code,
			"message": error_message,
			"response": response_text
		}
	}
	exc_type, exc_value, exc_traceback = sys.exc_info()
	if exc_traceback:
		error_dict["error"]["file"] = exc_traceback.tb_frame.f_code.co_filename
		error_dict["error"]["line"] = exc_traceback.tb_lineno
		error_dict["error"]["traceback"] = traceback.format_exc()
	if hasattr(e, "args"):
		error_dict["error"]["args"] = e.args
	if hasattr(e, "__dict__"):
		error_dict["error"]["attributes"] = e.__dict__
	return error_dict


async def chat_completion_json(request_data, chat_file):
	params = extract_request_data(request_data)
	model = params.get('model', None)
	log_me_request(chat_file, model, request_data)
	# fixme don't hardcode this, coz the user has to start the LM Studio server:
	client = OpenAI(base_url="http://localhost:5506/v1", api_key="lm-studio")
	response = client.chat.completions.create(**params)
	response_dict = response.to_dict()
	log_ai_response(chat_file, model, response_dict)
	return response_dict


async def chat_completion_stream(request_data, chat_file):
	params = extract_request_data(request_data)
	model = params.get('model', None)
	log_me_request(chat_file, model, request_data)
	# fixme don't hardcode this, coz the user has to start the LM Studio server:
	client = OpenAI(base_url="http://localhost:5506/v1", api_key="lm-studio")
	response = client.chat.completions.create(**params)
	result = ""
	for chunk in response:
		result += getattr(chunk.choices[0].delta, 'content') or ''
		transformed_chunk = chunk.to_dict()
		yield f"data: {json.dumps(transformed_chunk)}\n\n".encode("utf-8")
	yield b"data: [DONE]\n\n"
	log_ai_response(chat_file, model, result)


'''
curl http://localhost:8000/v1/chat/completions \
	-H "Content-Type: application/json" \
	-d '{ 
		"model": "lmstudio",
		"messages": [ 
			{ "role": "system", "content": "Always answer in rhymes." },
			{ "role": "user", "content": "Introduce yourself." }
		], 
		"temperature": 0.7, 
		"max_tokens": -1,
		"stream": true
}'

LM Studio with only 1 model available, at a time:
curl http://localhost:5506/v1/chat/completions \
	-H "Content-Type: application/json" \
	-d '{ 
		"model": "lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF",
		"messages": [ 
			{ "role": "system", "content": "You are a helpful assistant." },
			{ "role": "user", "content": "Hello! Who are you?" }
		], 
		"temperature": 0.7, 
		"max_tokens": -1,
		"stream": true
}'
... response:
{
	"id": "chatcmpl-39auomzninlyt5nmlqhki",
	"object": "chat.completion",
	"created": 1718544917,
	"model": "lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf",
	"choices": [
	{
		"index": 0,
		"message": {
		"role": "assistant",
		"content": "Nice to meet you! I'm a large language model trained by a team of researcher at Meta AI. My primary function is to assist and communicate with humans in a natural and helpful way, using a conversational interface. I can answer questions, provide information on a wide range of topics, and even generate text based on your input. I'm here to help you with any questions or tasks you may have! How can I assist you today?"
		},
		"finish_reason": "stop"
	}
	],
	"usage": {
	"prompt_tokens": 28,
	"completion_tokens": 89,
	"total_tokens": 117
	}
}
'''

