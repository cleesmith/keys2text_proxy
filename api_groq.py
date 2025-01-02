# aidetour_groq.py
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

from groq import Groq


def word_count(s):
    return len(re.findall(r'\w+', s))

def extract_request_data(request_data):
    # initialize a dictionary with all possible OpenAI API request parameters
    params = {
        "messages": request_data.get('messages'),
        "model": request_data.get('model'),
        "frequency_penalty": request_data.get('frequency_penalty'),
        # not supported by Groq api:
        # "logprobs": request_data.get('logprobs'),
        # "logit_bias": request_data.get('logit_bias'),
        # "top_logprobs": request_data.get('top_logprobs'),
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
        if hasattr(backend_response, 'choices') and backend_response.choices:
            content = backend_response.choices[0].message.content
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

def response_to_dict(response):
    # convert response object to a dictionary with the specified structure
    response_dict = {
        "id": response.id,
        "object": response.object,
        "created": response.created,
        "model": response.model,
        "choices": [
            {
                "index": choice.index,
                "finish_reason": choice.finish_reason,
                "message": {
                    "content": choice.message.content,
                    "role": choice.message.role
                }
            }
            for choice in response.choices
        ]
    }
    # print(f"\n******\nresponse_dict: type={type(response_dict)}:\n{response_dict}\n*****\n")
    return response_dict


async def chat_completion_json(request_data, chat_file):
    params = extract_request_data(request_data)
    model = params.get('model', None)
    log_me_request(chat_file, model, request_data)
    # fixme getting api key from environment var via os.environ.get("")
    client = Groq()
    response = client.chat.completions.create(**params)
    # print(f"\n*****\nresponse: type={type(response)}:\n{response}\n*****\n")
    log_ai_response(chat_file, model, response)
    return response_to_dict(response)


async def chat_completion_stream(request_data, chat_file):
    params = extract_request_data(request_data)
    model = params.get('model', None)
    log_me_request(chat_file, model, request_data)
    # fixme getting api key from environment var via os.environ.get("")
    client = Groq(max_retries=0, timeout=60)
    response = client.chat.completions.create(**params)
    result = ""
    for chunk in response:
        result += getattr(chunk.choices[0].delta, 'content') or ''
        # extract the content from the Choice object
        transformed_chunk = {
            "id": chunk.id,
            "object": chunk.object,
            "created": chunk.created,
            "model": chunk.model,
            "choices": [
                {
                    "index": choice.index,
                    "delta": {
                        "role": choice.delta.role,
                        "content": choice.delta.content,
                    } if choice.delta else None,
                    "finish_reason": choice.finish_reason,
                }
                for choice in chunk.choices
            ]
        }
        yield f"data: {json.dumps(transformed_chunk)}\n\n".encode("utf-8")
        # raise Exception
    yield b"data: [DONE]\n\n"
    log_ai_response(chat_file, model, result)


'''
https://console.groq.com/docs/openai
OpenAI Compatibility
Groq's APIs are designed to be compatible with OpenAI's, with the goal of 
making it easy to leverage Groq in applications you may have already built. 
However, there are some nuanced differences where support is not yet available.

Text Completion
The following fields are not supported and will result in a 400 error if they are supplied:

logprobs
logit_bias
top_logprobs


If N is supplied, it must be equal to 1.

messages[].name The name field is not supported by any of our models.

Temperature
If you set a temperature value of 0, it will be converted to 1e-8. 
If you run into any issues, please try setting the value to a float32 > 0 and <= 2.

URL
The base_url is https://api.groq.com/openai/v1
'''

'''
test directly to Groq:
curl -X POST "https://api.groq.com/openai/v1/chat/completions" \
     -H "Authorization: Bearer $GROQ_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"messages": [{"role": "user", "content": "hi!"}], "model": "llama3-8b-8192", "stream": true}'


get a list of models from Groq:
curl -X GET "https://api.groq.com/openai/v1/models" \
     -H "Authorization: Bearer $GROQ_API_KEY" \
     -H "Content-Type: application/json"

{"object":"list","data":[{"id":"gemma-7b-it","object":"model","created":1693721698,"owned_by":"Google","active":true,"context_window":8192},{"id":"llama3-70b-8192","object":"model","created":1693721698,"owned_by":"Meta","active":true,"context_window":8192},{"id":"llama3-8b-8192","object":"model","created":1693721698,"owned_by":"Meta","active":true,"context_window":8192},{"id":"mixtral-8x7b-32768","object":"model","created":1693721698,"owned_by":"Mistral AI","active":true,"context_window":32768}]}


test this code:
curl -i -X POST -H "Content-Type: application/json" -d '{                     
  "model": "llama3-70b-8192",
  "messages": [        
    {                                          
      "role": "system",
      "content": "You are a helpful assistant."
    },               
    {                                 
      "role": "user",
      "content": "Hello, how are you?"
    }           
  ],
  "stream": true
}' http://localhost:8000/v1/chat/completions
'''
