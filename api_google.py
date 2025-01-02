# api_gemini.py
import os
import sys
import traceback
import re
import textwrap
import json
import time
import datetime
import uuid
from fastapi import Request
from fastapi.responses import StreamingResponse, JSONResponse

# pip install google-generativeai
import google.generativeai as genai
from google.generativeai.types.generation_types import GenerateContentResponse

default_model = 'gemini-1.5-pro'

async def google_models():
	try:
		genai.configure(api_key=os.environ['GEMINI_API_KEY'])
		models = []
		for model in genai.list_models(request_options={"timeout": 5.0}):
			models.append(model.name)
		return sorted(models)
	except Exception as e:
		return None

def word_count(s):
	return len(re.findall(r'\w+', s))

def generate_unique_string():
	unique_id = str(uuid.uuid4())
	unique_id = unique_id.replace("-", "")
	unique_id = unique_id[:24]
	unique_string = "msg_" + unique_id
	return unique_string

def convert_request_for_gemini(request_data):
	print(f"\n convert_request_for_gemini:\n request_data: type={type(request_data)}:\n{request_data}\n")
	# modify the system messages and wrap them in asterisks
	request_data['messages'] = [
		{'role': 'user', 'content': f"*{msg['content']}*"}
		if msg['role'] == 'system'
		else msg
		for msg in request_data['messages']
	]
	# construct the new request dict for Gemini
	request_dict = {
		"contents": [
			{
				"role": "user",
				"parts": [
					{
						"text": msg['content']
					}
				]
			}
			for msg in request_data['messages']
		],
		# i'm using None, but False works too, even better, if missing then False is the default:
		# "stream": request_data.get('stream', None),
		"generation_config": {
			"candidate_count": 1,
			"max_output_tokens": request_data.get('max_tokens', None),
			"temperature": request_data.get('temperature', None),
		}
	}
	# remove any parameters that are None
	request_dict = {key: value for key, value in request_dict.items() if value is not None}
	print(f"\n convert_request_for_gemini:\nrequest_dict: type={type(request_dict)}:\n{request_dict}\n")
	return request_dict


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
	# print(f"\nlog_me_request: user_request: {type(user_request)}\n{user_request}\n")
	timestamp = datetime.datetime.now().strftime("%A, %b %d, %Y - %I:%M %p")
	messages = user_request['messages']
	messages_string = messages_to_string(messages)
	# content = "\n".join([msg['content'] for msg in messages])
	formatted_output, words = format_text(messages_string)
	with open(chat_file_name, "a") as f:
		words = word_count(formatted_output)
		f.write(f"\n\nME:   {timestamp}  {model}  {words} words\n")
		f.write(formatted_output)
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

def generate_content_response_to_dict(response, model):
	message_id = generate_unique_string()
	response_dict = {
		"id": message_id,
		"object": "chat.completion",
		"created": int(time.time()),
		"model": model,
		"choices": [{
			"index": 0,
			"message": {
				"role": "assistant",
				"content": response.text,
			},
			"finish_reason": "stop"
		}]
	}
	return response_dict


async def chat_completion_json(request_data, chat_file):
	model = request_data.get('model', default_model)
	params = convert_request_for_gemini(request_data)
	log_me_request(chat_file, model, request_data)
	genai.configure(api_key=os.environ['GEMINI_API_KEY'])
	client = genai.GenerativeModel(model)
	response = client.generate_content(**params)
	response_dict = generate_content_response_to_dict(response, model)
	log_ai_response(chat_file, model, response_dict)
	return response_dict


async def chat_completion_stream(request_data, chat_file):
	model = request_data.get('model', default_model)
	params = convert_request_for_gemini(request_data)
	log_me_request(chat_file, model, request_data)
	genai.configure(api_key=os.environ['GEMINI_API_KEY'])
	client = genai.GenerativeModel(model)
	response = client.generate_content(**params, stream=True)
	c = 1
	message_id = generate_unique_string()
	result = ""
	for chunk in response:
		result += chunk.text or ""
		message_id = f"{c}.{generate_unique_string()}"
		transformed_data = {
			"id": message_id,
			"object": "chat.completion.chunk",
			"created": int(time.time()),
			"model": model,
			"choices": [{
				"index": 0,
				"delta": {
					"role": "assistant",
					"content": chunk.text,
				},
				"finish_reason": None
			}]
		}
		yield f"data: {json.dumps(transformed_data)}\n\n"
		c = c + 1

	message_id = f"{c}.{generate_unique_string()}"
	transformed_data = {
		"id": message_id,
		"object": "chat.completion.chunk",
		"created": int(time.time()),
		"model": model,
		"choices": [{
			"index": 0,
			"delta": {},
			"finish_reason": "stop"
		}]
	}
	yield f"data: {json.dumps(transformed_data)}\n\n"
	yield "data: [DONE]\n\n"
	log_ai_response(chat_file, model, result)

