# api_anthropic.py
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

import anthropic
from anthropic import Anthropic


async def anthropic_models():
	try:
		client = anthropic.Anthropic(
			api_key=os.environ['ANTHROPIC_API_KEY'],
			max_retries=0,
		)
		models = client.models.list(limit=1000) # default=20
		model_ids = [model.id for model in models.data]
		sorted_models = sorted(model_ids)
		return sorted_models
	except Exception as e:
		return None

def word_count(s):
	return len(re.findall(r'\w+', s))

def extract_chat_params(request_data):
	params = {
		'model': request_data['model'],
		'messages': [msg for msg in request_data['messages'] if msg['role'] != 'system'],
		'max_tokens': max(1, request_data.get('max_tokens', 4000))  # ensure min value of 1
	}
	# handle temperature (0.0 to 1.0)
	if 'temperature' in request_data:
		temp = request_data['temperature']
		if isinstance(temp, (int, float)) and 0 <= temp <= 1:
			params['temperature'] = temp
	# handle top_p (integer)
	if 'top_p' in request_data:
		top_p = request_data['top_p']
		if isinstance(top_p, int):
			params['top_p'] = top_p
	system_message = next((msg['content'] for msg in request_data['messages'] if msg['role'] == 'system'), None)
	if system_message:
		params['system'] = system_message
	return params

def format_chat_response(response, params_model):
	return {
		"id": response.id,
		"object": "chat.completion",
		"created": int(time.time()),
		"model": getattr(response, 'model', params_model),
		"choices": [
			{
				"index": 0,
				"message": {
					"role": "assistant",
					"content": response.content[0].text if response.content else ""
				},
				"finish_reason": response.stop_reason
			}
		]
	}

def format_error_response(error, params_model):
	if isinstance(error, anthropic.APIStatusError):
		error_type = "api_error"
		status_code = error.status_code
		response_text = error.response.text() if callable(getattr(error.response, 'text', None)) else getattr(error.response, 'text', None)
	else:
		error_type = "unexpected_error"
		status_code = 500
		response_text = None
	error_message = str(error)
	return {
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
			# If there are already line breaks, use them to split paragraphs
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
		f.flush()

def log_ai_response(chat_file_name, model, backend_response):
	timestamp = datetime.datetime.now().strftime("%A, %b %d, %Y - %I:%M %p")
	# log backend_response as AI:
	with open(chat_file_name, "a") as f:
		if hasattr(backend_response, 'content'):
			# extract the text from the backend_response object before passing to format_text
			text_to_format = backend_response.content[0].text if hasattr(backend_response.content[0], 'text') else str(backend_response.content[0])
		else:
			text_to_format = backend_response
		formatted_text, words = format_text(text_to_format)
		f.write(f"\n\nAI:   {timestamp}  {model}  {words} words\n")
		f.write(formatted_text)
		f.flush()
	return

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
	return


async def chat_completion_json(request_data, chat_file):
	# https://github.com/anthropics/anthropic-sdk-python/blob/2dfb899e34a785343ef07ad4cd0ddde8d37a7f74/README.md?plain=1#L279
	client = Anthropic(
		api_key=os.environ.get("ANTHROPIC_API_KEY"), 
		max_retries=0,
		timeout=60.0
	)
	params = extract_chat_params(request_data)
	model = params.get('model', None)
	log_me_request(chat_file, model, request_data)
	try:
		# instead of making the actual API call, we'll raise the error manually
		# if True:
		# 	class MockRequest:
		# 		method = "POST"
		# 		url = "https://api.anthropic.com/v1/messages"
		# 		headers = {"Content-Type": "application/json"}
		# 		body = '{"messages": [{"role": "user", "content": "Hello"}]}'
		# 	class MockResponse:
		# 		status_code = 529
		# 		request = MockRequest()
		# 		def json(self):
		# 			return {"error": {"message": "Service overloaded"}}
		# 		def text(self):
		# 			return '{"error": {"message": "Service overloaded"}}'
		# 	raise anthropic.APIStatusError(
		# 		message="Service overloaded",
		# 		response=MockResponse(),
		# 		body={"error": {"message": "Service overloaded"}}
		# 	)
		response = client.messages.create(**params)
		log_ai_response(chat_file, model, response)
		return format_chat_response(response, model)
	except anthropic.APIStatusError as e:
		log_ai_response_error(chat_file, model, e)
		return format_error_response(e, model)
	except Exception as e:
		log_ai_response_error(chat_file, model, e)
		return format_error_response(e, model)


async def chat_completion_stream(request_data, chat_file):
	# https://github.com/anthropics/anthropic-sdk-python/blob/2dfb899e34a785343ef07ad4cd0ddde8d37a7f74/README.md?plain=1#L279
	client = Anthropic(
		api_key=os.environ.get("ANTHROPIC_API_KEY"), 
		max_retries=0,
		timeout=60.0
	)
	params = extract_chat_params(request_data)
	model = params.get('model', None)
	log_me_request(chat_file, model, request_data)
	error = ""
	stream = None
	try:
		with client.messages.stream(**params) as stream:
			for text in stream.text_stream:
				sse_data = {
					"id": str(time.time()),  # using current timestamp as id
					"object": "chat.completion.chunk",
					"created": int(time.time()),
					"model": model,
					"choices": [{
						"index": 0,
						"delta": {
							"content": text
						},
						"finish_reason": None
					}]
				}
				yield f"data: {json.dumps(sse_data)}\n\n".encode("utf-8")

				# send the final chunk with finish_reason
				final_sse_data = {
				"id": "last",
				"object": "chat.completion.chunk",
				"created": int(time.time()),
				"model": model,
				"choices": [{
					"index": 0,
					"delta": {},
					"finish_reason": "stop"
				}]
				}
				yield f"data: {json.dumps(final_sse_data)}\n\n".encode("utf-8")
		yield b"data: [DONE]\n\n"
	except anthropic.APIStatusError as e:
		log_ai_response_error(chat_file, model, e)
		error = f"Error:\n{e}"
		yield f"data: {json.dumps(format_error_response(e, model))}\n\n".encode('utf-8')
		yield "data: [DONE]\n\n".encode('utf-8')
	except Exception as e:
		log_ai_response_error(chat_file, model, e)
		error = f"Error:\n{e}"
		yield f"data: {json.dumps(format_error_response(e, model))}\n\n".encode('utf-8')
		yield "data: [DONE]\n\n".encode('utf-8')

	if stream is not None:
		final_message = stream.get_final_message()
		content = final_message.content
		text = content[0].text
		cleaned_text = re.sub(r'\*+', '', text)
	else:
		cleaned_text = error
	log_ai_response(chat_file, model, cleaned_text)

