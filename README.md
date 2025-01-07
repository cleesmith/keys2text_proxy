# Keys2Text Proxy

Keys2Text Proxy is a Python-based application that acts as an **API proxy server**, 
offering **full OpenAI API compatibility** while seamlessly routing requests to multiple 
AI providers using your own API keys. You can use the familiar OpenAI endpoints in your 
existing code and effortlessly switch between providers—Anthropic, Google AI Studio, Groq, 
OpenRouter, DeepSeek, LM Studio, Ollama, or OpenAI itself—**simply by configuring your API keys**.

## Key Features

- **Free and Open-source forever**  
  Keys2Text Proxy is a Python FastAPI based app that is free and open-sourced.<br>
  After all, it only exists because of the AI providers and their APIs.

- **Full OpenAI API Compatibility**  
  Mimics OpenAI's endpoints and request/response formats, but only the text-based chat completion endpoints.<br>
  And now that each AI provider returns a list of available models by using `client.models.list()` the app can stay up-to-date with model releases.

- **Multi-Provider Support**  
   Supply your own API keys to these services, and the proxy will handle the request translation behind the scenes.<br>
   The API keys are found if/when you've exported them into the environment.

  With Keys2Text Proxy, you can easily connect to:
  - **OpenAI**  
  - **Anthropic (Claude)**  
  - **Google AI Studio (Gemini)**  *free as of Jan 2025*
  - **Groq**    *free as of Jan 2025*
  - **OpenRouter**    *a few free models as of Jan 2025*
  - **DeepSeek**  
  - **LM Studio**  
  - **Ollama**

- **Timestamped Chat History as plain text file**  
  The app keeps a *plain text log* of all requests and responses for reference and as an aid in writing.<br>
  Conversations are saved with timestamps and paired using `Me:` and `AI:` labels.<br>
  A new text file is created whenever the app is started up, which allows for organizing <br>
  your AI chats simply by starting, stopping, and restarting this app.<br>
  This was the result of a personal itch; I find repeatedly doing copy/paste's tedious, as it's<br>
  much easier to just have everything then do editing.

## How It Works

1. **Local HTTP Server**  
   Keys2Text Proxy starts an HTTP server (default: `http://localhost:8000`) with <br>
   routes matching the OpenAI API —-for example, `/v1/chat/completions`.

2. **Request Translation**  
   When a request arrives (in OpenAI-compatible format), the proxy translates it to <br>
   the corresponding provider’s format using the model named in the request.

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
     LM_STUDIO_API_KEY=<no-api-key-required-so-anything-works>
     
     # Ollama
     OLLAMA_API_KEY=<no-api-key-required-so-anything-works>
     ```
   - Each key is only used if/when you send requests to a model from that provider.

3. **Run the Proxy**  
   ```bash
   uvicorn keys2text_proxy:app --workers 1 --host localhost --port 8000
   ```
   By default, the server runs on `http://localhost:8000`. <br>
   You can now direct any OpenAI-compatible client to this URL, well maybe,<br>
   as I have only used this app with `novelcrafter` (read more under Usage).


## Usage

- **This app is a personal proxy server**

  Keys2Text Proxy is intended to be run locally, i.e. on your computer, and not in the <br>
  cloud/internet which may violate the AI providers API `Terms of Service/Use` (*maybe*).<br>
  While there are advantages to running it locally; this app will probably only <br>
  run on desktops and laptops.

- **novelcrafter**

  Keys2Text was written for and tested using [novelcrafter](https://www.novelcrafter.com)<br>
  Keys2Text handles CORS so your web browser can perform behind the scenes local `fetch`-es to Keys2Text Proxy server.<br>

> Personally, for `novelcrafter` settings I use `LM Studio` in `AI Connections` and change the port.<br>
  When using API keys for all of the AI providers, the list of models is over 300, which is wow and unweildy.<br>

> Works great:<br>
  🏴‍☠️ and I'm my own middle-man<br> 
  🐢 it's not any slower or quirkier in responding than the usual chatters<br>
  👽 issues are between me and the AI provider (*429's and such*) and handled via their support (*if ever*)<br>
  🔐 my API keys are directly used with AI providers (more secure), and no extra usage fees<br>
  💸💰 yes, you still pay for API usage (*when not free*)<br><br>
  😱 No offense to the ever growing number of cloud providers offering a similar service.

- **Chat Logging**  

  Every conversation is automatically logged in a timestamped text file, e.g., `chat_YYYY-MM-DD_HH-MM-SS.txt`.<br>
  This log is just a plain text file tracking your prompts as pairs of `Me:` prompt and `AI:` response,<br>
  which may be helpful for writers and editing.

## Roadmap

- **Additional Providers**  
  While we (*who we? 🤔*) already support several popular AI services, <br>
  the proxy is designed to be extended easily (*well, if you can code python/fastapi/generator-yielding/streaming-nonstreaming-apis/wrangle-json-and-text, then sure*).<br> 
  We plan to continually add new integrations.<br> 
  Do *we*, maybe, perhaps a new AI provider will emerge someday or overnight.🥸

- **Advanced Features**  
  Next in the hopper 🎡:<br>
  🤖 NER (name entity recognition) for existing writing<br>
  ⏪🤖 reverse-NER for story outlining<br>
  📜 ✍🏽 both are kind of `codex` related (see `novelcrafter`)

## Contributing

We welcome contributions (*we do?*), bug 🐞 reports, and feature 🍿 requests. <br>
Please open an issue or submit a pull request on GitHub.

## License

This project is licensed under the [MIT License](LICENSE).

---

With **Keys2Text Proxy**, you can unify your AI workflows under a single, <br>
OpenAI-compatible interface—while retaining the freedom to choose any provider that best fits your needs. 

---


Enjoy! ☮️
