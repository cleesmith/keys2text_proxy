# Keys2Text Proxy

Keys2Text Proxy is a Python-based application that acts as an **API proxy server**, 
offering **full OpenAI API compatibility** while seamlessly routing requests to multiple 
AI providers using your own API keys. You can use the familiar OpenAI endpoints in your 
existing code and effortlessly switch between providers—Anthropic, Google AI Studio, Groq, 
OpenRouter, DeepSeek, LM Studio, Ollama, or OpenAI itself—**simply by configuring your API keys**.

## Intro blurb used on novelcrafter's discord

> Keys2Text Proxy is a Python FastAPI application that lets you use multiple AI providers (OpenAI, Anthropic, Google AI Studio, Groq, OpenRouter, DeepSeek, LM Studio, and Ollama) through a single OpenAI-compatible proxy server using your own API keys. It runs locally on your computer, saves chat history as plain text, and works nicely with NovelCrafter. The code is open source and free to use.

## Key Features

- **Free and Open-source forever**  
  Keys2Text Proxy is a Python FastAPI based app that is free and open-sourced.<br>
  This technology relies on two key foundations: the essential infrastructure provided by AI companies and their APIs, along with innovative writing tools like novelcrafter that help bring these capabilities to life.

- **Full OpenAI API Compatibility**  
  Mimics OpenAI's endpoints and request/response formats, but only the text-based chat completion endpoints.<br>
  And now that each AI provider returns a list of available models by using `client.models.list()` the app can stay up-to-date with model releases.

- **Multi-Provider Support**  
   Supply your own API keys to these services, and the proxy will handle the request translation behind the scenes.<br>
   The API keys are found if/when you've exported them into the environment.

  With Keys2Text Proxy, you can easily connect to:
  - **OpenAI**  
  - **Anthropic (Claude)**  
  - **Google AI Studio (Gemini)** &nbsp;&nbsp;&nbsp;*free as of Jan 2025*
  - **Groq** &nbsp;&nbsp;&nbsp;*free as of Jan 2025*
  - **OpenRouter** &nbsp;&nbsp;&nbsp;*a few free models as of Jan 2025*
  - **DeepSeek**  
  - **LM Studio**  
  - **Ollama**

- **Timestamped Chat History as plain text file**  
  - The app keeps a *plain text log* of all requests and responses for reference and as an aid in writing.<br>
  - Conversations are saved with timestamps and paired using `Me:` and `AI:` labels.<br>
  - A new text file is created whenever the app is started up, which allows for organizing <br>
  your AI chats simply by starting, stopping, and restarting this app.
> This was the result of a personal itch; I find repeatedly doing copy/paste's tedious, as it's<br>
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

---

## Installation

**Pick your ☠️ poison** based on your setup:<br>
- Option 1: Install via **pip** (if you already have Python)
- Option 2: Install via **Miniconda** (for a fresh start)

### Option 1: Install via pip

1. Open a terminal (mac) or Command Prompt (Windows).
2. Run:
   ```bash
   python --version
   pip --version
   ```
   ```bash
   pip install keys2text_proxy
   ```
3. Start the proxy:
   ```bash
   keys2text_proxy
   ```
   *Note: this will fail if you do not already have API keys defined in your environment.*


### Option 2: Install via Miniconda to install python/pip in a separate environment

#### Windows 💾

1. Open **Command Prompt**.
2. Run:
   ```batch
   curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe -o miniconda.exe
   start /wait "" .\miniconda.exe /S
   del miniconda.exe
   ```
3. Make a new folder, create a conda environment, and install Keys2Text Proxy:
   ```batch
   mkdir someFolder
   cd someFolder
   conda create -n keysapp python=3.11
   conda activate keysapp
   pip install keys2text_proxy
   keys2text_proxy
   ```

#### macOS 🍎

1. Open **Terminal**.
2. Run:
   ```bash
   mkdir -p ~/miniconda3
   curl https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh -o ~/miniconda3/miniconda.sh
   bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
   rm ~/miniconda3/miniconda.sh
   ```
3. Initialize your shell:
   ```bash
   source ~/miniconda3/bin/activate
   conda init --all
   ```
4. Close and reopen Terminal, then:
   ```bash
   mkdir someFolder
   cd someFolder
   conda create -n keysapp python=3.11
   conda activate keysapp
   pip install keys2text_proxy
   keys2text_proxy
   ```

---

## Troubleshooting 😈

- **Windows**: If you get permission errors, try running Command Prompt as administrator.
- **macOS**: If conda isn’t recognized, make sure you ran `conda init --all` and then **reopened** your terminal.
- **Conda environment**: Double-check you’ve activated it (`conda activate keysapp`) before starting the proxy.


After configuring your API keys, Keys2Text Proxy will start on your machine, ready for NovelCrafter or any other app that needs it.

---

2. **Configuration of API 🗝️ keys**  
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
   keys2text_proxy
   ```
   By default, the server runs on `http://localhost:8000`. <br>

> You can now direct any OpenAI-compatible client to this URL, well maybe,<br>
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

> So far it all works great together:<br>
  🏴‍☠️ and I'm my own middle-man<br> 
  🐢 the proxy is not any slower or quirkier in responding than the usual chatters<br>
  👽 any issues are between me and the AI provider (*429's and such*) and handled via their support (*if ever*)<br>
  🔐 my API keys are directly used with AI providers (more secure), and no extra usage fees<br>
  💰 yes, you still pay for API usage (*when not free*) via your API keys directly to the AI provider<br><br>
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
  📜 ✍🏽 both are kind of `codex` related (like in `novelcrafter`)

## Contributing

We welcome contributions (*we do?*), bug 🐞 reports, and feature 🍿 requests. <br>
Please open an issue or submit a pull request on GitHub.

## License

This project is licensed under the [MIT License](LICENSE).

---

With **Keys2Text Proxy**, you can unify your AI workflows under a single, <br>
OpenAI-compatible interface—while retaining the freedom to choose any provider that best fits your needs. 

> *If any of the above reads like AI writing, like all of that "we" talk, there is only "I" ... 🙋🏽‍♂️ guilty.*

---


Enjoy! ☮️
