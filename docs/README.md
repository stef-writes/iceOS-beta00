# ICE.OS

A modular, multi-provider workflow engine for orchestrating and chaining LLM (Large Language Model) calls across providers like OpenAI, Anthropic, Google Gemini, and DeepSeek.

---

## Overview
ICE.OS enables you to build, test, and deploy complex LLM-powered workflows using a node-based architecture. It abstracts away provider-specific quirks, supports flexible chaining, and exposes a FastAPI backend for easy integration.

---

## Features
- **Multi-Provider Support:** OpenAI, Anthropic, Google Gemini, DeepSeek (extensible to more)
- **Node-Based Workflow Engine:** Compose chains of LLM calls and operations
- **Provider-Agnostic API:** Unified interface for different LLMs
- **Extensible:** Add new providers, nodes, or utilities easily
- **Testable:** Comprehensive test suite and fixtures
- **Modern Python:** Async, Pydantic, FastAPI, type hints

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd ice.os
   ```
2. **Set up a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Quickstart

See [QUICKSTART.md](QUICKSTART.md) for detailed setup and usage instructions.

To start the API server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at [http://localhost:8000](http://localhost:8000)

---

## Folder Structure

See [CODEBASE_INFO.md](CODEBASE_INFO.md) for a detailed breakdown of the codebase structure and file descriptions.

---

## Testing

Run the test suite:
```bash
python tests/openai_chain_test.py
```

---

## Contributing

1. Fork the repo and create your branch (`git checkout -b feature/fooBar`)
2. Commit your changes (`git commit -am 'Add some fooBar'`)
3. Push to the branch (`git push origin feature/fooBar`)
4. Create a new Pull Request

---

## License

MIT License. See `LICENSE` file for details.

---

## Authors & Credits

- [Your Name or Team]
- Inspired by the open-source LLM ecosystem

---

## Market Opportunity & Vision

See [SCRIPTCHAIN_ANALYSIS.md](SCRIPTCHAIN_ANALYSIS.md) for a strategic and technical analysis of ICE.OS's potential as a startup seed.

---

## Tool/Function Calling API Requirements

- **Tool schemas are backend-driven:**
  - When defining a node that uses tools/functions (for OpenAI function calling or similar), only specify the tool `name` and `description` in your node config or POST body.
  - **Do NOT** provide parameter schemas or example values in your POST. These will be ignored.
  - The backend will always inject the correct JSON Schema for each tool/function from the tool registry at runtime.
  - This ensures all schemas are valid and compatible with LLM providers (e.g., OpenAI).
  - If you attempt to register or POST a tool with an invalid schema, the backend will return a clear error.

**Example NodeConfig POST (tools section):**
```json
{
  "id": "parser-node-1",
  "type": "ai",
  "model": "gpt-4",
  "prompt": "Parse the transcript using the transcript_parser tool.",
  "dependencies": [],
  "llm_config": {
    "provider": "openai",
    "model": "gpt-4"
  },
  "tools": [
    {
      "name": "transcript_parser",
      "description": "Parses a raw transcript into utterances."
    }
  ],
  "input_schema": {"raw_transcript_text": "str"},
  "output_schema": {"utterances": "list"}
}
```

- The backend will automatically attach the correct JSON Schema for `transcript_parser` at runtime.
- This makes your API usage future-proof and robust for all tool/function calling scenarios. 