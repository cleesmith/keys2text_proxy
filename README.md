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
- A graphical user interface (GUI) for both macOS and Windows
- A command-line interface (CLI) mode for terminal usage
- A timestamped chat log of your requests plus Claude's responses, as pairs of "Me:" and "AI:"
- Logging functionality for tracking application events and errors

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
python keys2text_proxy.py
```

The application will start the API server and listen for incoming requests.

## Configuration


## Contributing

If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.
