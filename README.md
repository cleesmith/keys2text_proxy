# Keys2Text Proxy

Keys2Text Proxy is a Python-based application that acts as an **API proxy server**, 
offering **full OpenAI API compatibility** while seamlessly routing requests to multiple 
AI providers using your own API keys. You can use the familiar OpenAI endpoints in your 
existing code and effortlessly switch between providers—Anthropic, Google AI Studio, Groq, 
OpenRouter, DeepSeek, LM Studio, Ollama, or OpenAI itself—**simply by configuring your API keys**.

## Key Features

- **Full OpenAI API Compatibility**  
  Mimics OpenAI's endpoints and request/response formats.

- **Multi-Provider Support**  
   Supply your own API keys to these services, and the proxy will handle 
   the request translation behind the scenes.

  With Keys2Text Proxy, you can easily connect to:
  - **OpenAI**  
  - **Anthropic (Claude)**  
  - **Google AI Studio (Gemini)**  
  - **Groq**  
  - **OpenRouter**  
  - **DeepSeek**  
  - **LM Studio**  
  - **Ollama**


- **Timestamped Chat History as plain text file**  
  The app keeps a plain-text log of all requests and responses for reference and as an aid in writing.
  Conversations are saved with timestamps and paired using `Me:` and `AI:` labels.
  A new text file is created whenever the app is started up, which allows for organizing 
  your AI chats simply by starting, stopping, and restarting this app.

## How It Works

1. **Local HTTP Server**  
   Keys2Text Proxy starts an HTTP server (default: `http://localhost:8000`) with routes matching 
   the OpenAI API—for example, `/v1/chat/completions`.

2. **Request Translation**  
   When a request arrives (in OpenAI-compatible format), the proxy translates it to 
   the corresponding provider’s format.

3. **Response Translation**  
   The provider’s response is then converted back into the OpenAI-like responses.

4. **Provider-Specific API Keys**  
   Users configure environment variables, API keys, for their preferred AI services. 

## Getting Started

1. **Installation**  
   ```bash
   git clone https://github.com/yourusername/keys2text-proxy.git
   cd keys2text-proxy
   pip install -r requirements.txt
   ```

2. **Configuration**  
   - Copy or rename `.env.example` to `.env`.
   - Insert your API keys for each provider you wish to use. For example:
     ```plaintext
     # Example .env
     # OpenAI
     OPENAI_API_KEY=<your-openai-api-key>
     
     # Anthropic
     ANTHROPIC_API_KEY=<your-anthropic-api-key>
     
     # Google AI Studio
     GOOGLE_AI_STUDIO_API_KEY=<your-google-ai-studio-api-key>
     
     # Groq
     GROQ_API_KEY=<your-groq-api-key>
     
     # OpenRouter
     OPENROUTER_API_KEY=<your-openrouter-api-key>
     
     # DeepSeek
     DEEPSEEK_API_KEY=<your-deepseek-api-key>
     
     # LM Studio
     LM_STUDIO_API_KEY=<your-lm-studio-api-key>
     
     # Ollama
     OLLAMA_API_KEY=<your-ollama-api-key>
     ```
   - Each key is only used if/when you send requests to the corresponding provider.

3. **Run the Proxy**  
   ```bash
   uvicorn keys2text_proxy:app --workers 1 --host localhost --port 8000
   ```
   By default, the server runs on `http://localhost:8000`. 
   You can now direct any OpenAI-compatible client to this URL.


## Usage

- **Programmatic**  
  Point your favorite OpenAI-based code or libraries to the proxy server:
  ```python
  import openai
  
  # Tell the OpenAI client library to talk to your local Keys2Text Proxy
  openai.api_base = "http://localhost:8000/v1"
  
  # Optionally, set a placeholder for openai.api_key (not used by the proxy):
  openai.api_key = "YOUR_PLACEHOLDER_KEY"
  
  response = openai.ChatCompletion.create(
      model="claude-3-opus-20240229",  # or any model recognized by your chosen provider
      messages=[{"role": "user", "content": "Hello from Keys2Text!"}]
  )
  print(response)
  ```
  The proxy will route the request to Anthropic (in this example), translating messages and responses into the OpenAI style.

- **Chat Logging**  
  Every conversation is automatically logged in a timestamped text file, e.g., `chatlog_YYYYMMDD_HHMMSS.txt`. This log tracks your prompts under `Me:` and responses under `AI:`.

## Roadmap

- **Additional Providers**  
  While we already support several popular AI services, the proxy is designed to be extended easily. We plan to continually add new integrations.

- **Advanced Features**  
  Future releases aim to include advanced configurations, caching, rate-limiting, and fine-tuning support to better manage complex workloads.

## Contributing

We welcome contributions, bug reports, and feature requests. 
Please open an issue or submit a pull request on GitHub.

## License

This project is licensed under the [MIT License](LICENSE).

---

With **Keys2Text Proxy**, you can unify your AI workflows under a single, OpenAI-compatible interface—while retaining the freedom to choose any provider that best fits your needs. 
Enjoy! ☮️










# Keys2Text Proxy

Keys2Text Proxy is a Python application that allows users to interact with Anthropic's 
Claude models using the same interface as the OpenAI API. Although it mimics 
the OpenAI API endpoints, Keys2Text Proxy does not actually use or require an OpenAI 
API key. Instead, it translates the requests and responses between the two APIs, 
enabling users to access Claude's capabilities through a familiar interface.

Keys2Text Proxy requires your Anthropic API key to function, as it communicates 
directly with the Anthropic Claude API behind the scenes.

## Key Features

- Seamless integration between a facade/mimicked OpenAI API and the real Anthropic Claude API
- Support for multiple Claude models:
  - Opus: claude-3-opus-20240229
  - Sonnet: claude-3-sonnet-20240229
  - Haiku: claude-3-haiku-20240307
- A command-line interface (CLI) mode for terminal usage
- A plain text timestamped chat file/log of your requests plus Claude's responses, as pairs of "Me:" and "AI:"

... the above needs rewriting as the app has grown beyond just Anthropic
... now it's a proxy api server offering full OpenAI API compatibility, while using 
each AI providers API with users api keys in the backend

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/cleesmith/keys2text_proxy.git
   ```

2. Navigate to the project directory:
   ```
   cd keys2text_proxy
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run Keys2Text Proxy in CLI mode, use the `--cli` flag:
```
uvicorn keys2text_proxy:app --workers 1 --host localhost --port 8000
```

The application will start the API proxy server and listen for incoming requests.


## Contributing

If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.
