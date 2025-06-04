
---

### 1. **ScriptChain (Workflow Orchestration)**
- **Location:** `src/app/chains/script_chain.py`
- **Purpose:** Orchestrates execution of a directed acyclic graph (DAG) of nodes, supporting level-based parallel execution, dependency management, and robust error handling.
- **Key Features:**
  - Nodes are configured with dependencies; the chain builds a dependency graph and checks for cycles.
  - Nodes are grouped by "level" (topological sort), allowing parallel execution within a level.
  - Each node's output can be mapped to the context of dependent nodes, with explicit input mappings or fallback to direct output.
  - Global context is managed via a `GraphContextManager`.
  - Callbacks are supported for node/chain start, end, and error events.
  - Metrics (token usage, execution times, provider usage) are tracked.
  - Intelligent error handling: execution continues if possible, only halting if all remaining nodes are blocked by failed dependencies.

---

### 2. **Nodes (Base, AI, Factory, Prompt, Tool Call, Error Handling)**
- **Location:** `src/app/nodes/`
- **BaseNode:** Abstract class defining the interface for all nodes, with hooks for pre/post execution, input validation, and an abstract `execute` method.
- **AiNode:** Implements agentic LLM node logic:
  - Uses LLMs for text generation, supports tool/function calling via a "thought loop" (detects tool calls, executes tools, feeds results back to LLM, repeats up to max steps).
  - Prepares prompts with context, tool preambles, and templates.
  - Handles output parsing (tries JSON, falls back to schema-based extraction, or plain text).
  - Integrates with `LLMService` and `ToolService`.
- **Prompt Builder:** Functions to build tool preambles and prepare prompts, including context formatting and token limit checks.
- **Tool Call Utils:** Detects and formats tool/function call outputs for LLMs.
- **Error Handling:** Centralized error classification and formatting for LLM API errors.
- **Node Factory:** Instantiates nodes based on type (currently supports "ai" nodes).

---

### 3. **AI/LLM Providers**
- **Location:** `src/app/llm_providers/`
- **Structure:** Abstract base handler + concrete handlers for OpenAI, Anthropic, Google Gemini, DeepSeek.
- **Handler Responsibilities:**
  - Each handler implements an async `generate_text` method, taking LLM config, prompt, context, and optional tools.
  - Handles API key management, request construction, and response parsing (including function/tool call results).
  - Returns generated text, token usage stats, and error info.
- **LLMService:** Routes requests to the correct handler based on provider.

---

### 4. **Tools**
- **Location:** `src/app/tools/`
- **BaseTool:** Abstract class for all tools, requiring name, description, parameter schema (Pydantic), and a `run` method.
- **Example Tool:** Calculator (adds two numbers, validates input/output via Pydantic).
- **ToolService:** Manages tool registration, discovery, and async execution (with parameter validation, error handling, and timeouts). Tools are registered in a central registry and can be listed with their schemas for LLM function calling.

---

### 5. **Context Management**
- **Location:** `src/app/utils/context.py`
- **GraphContextManager:**
  - Manages persistent context for node execution, with support for max token limits, context formatting (text, JSON, markdown, code, custom), and context rules.
  - Context is stored in a JSON file (path configurable or default).
  - Provides methods to get/set/update/clear context for nodes, and to validate context rules.
  - Used by ScriptChain and nodes to persist and retrieve intermediate outputs and context.

---

### 6. **Other Utilities**
- **Token Counting:** Utilities for counting/estimating tokens for different providers/models.
- **Callbacks:** Abstract and concrete callback classes for logging and metrics during chain/node execution.
- **Tracking:** Token/cost tracking context manager and decorator.
- **Debugging:** Debug callback for detailed event logging.

---

**Summary of Interactions:**
- **ScriptChain** orchestrates node execution, manages dependencies, and persists context via `GraphContextManager`.
- **Nodes** (especially `AiNode`) use LLMs and tools, prepare prompts, and handle tool/LLM output in an agentic loop.
- **LLM Providers** are abstracted via handlers and a service, supporting multiple backends.
- **Tools** are modular, validated, and invoked asynchronously, with schemas exposed for LLM function calling.
- **Context** is persistently managed and formatted for LLM consumption, supporting complex workflows and chaining.

--w-up questions or requests for deeper dives
