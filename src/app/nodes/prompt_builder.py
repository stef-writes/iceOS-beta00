import json
from app.models.node_models import NodeConfig
from app.models.config import LLMConfig
from app.utils.token_counter import TokenCounter
from app.nodes.constants import TOOL_INSTRUCTION

# Standalone function for building the tool preamble

def build_tool_preamble(tools: list) -> str:
    """Generate a robust, LLM-friendly preamble describing available tools, their parameters, and usage examples."""
    if not tools:
        return ""
    lines = [
        "SYSTEM: You have access to the following tools:",
        ""
    ]
    for tool in tools:
        params = tool.get('parameters_schema', {}).get('properties', {})
        required = set(tool.get('parameters_schema', {}).get('required', []))
        param_strs = []
        example_args = {}
        for k, v in params.items():
            typ = v.get('type', 'unknown')
            desc = v.get('description', '')
            req = 'required' if k in required else 'optional'
            param_strs.append(f"{k} ({typ}, {req}){': ' + desc if desc else ''}")
            # Generate a realistic example value
            if typ == 'string':
                example_args[k] = f"example_{k}_value"
            elif typ == 'integer':
                example_args[k] = 1
            elif typ == 'number':
                example_args[k] = 1.0
            elif typ == 'boolean':
                example_args[k] = True
            elif typ == 'array':
                example_args[k] = []
            elif typ == 'object':
                example_args[k] = {}
            else:
                example_args[k] = f"example_{k}"
        param_str = ", ".join(param_strs) if param_strs else "No parameters."
        lines.append(f"- {tool['name']}: {tool['description']}\n  Parameters: {param_str}")
        # Add usage example (auto-generate if not present)
        usage_example = tool.get('usage_example')
        if not usage_example:
            usage_example = f'{{"function_call": {{"name": "{tool["name"]}", "arguments": {json.dumps(example_args, ensure_ascii=False)} }} }}'
        lines.append("  Example usage:")
        lines.append("    " + usage_example.strip().replace("\n", "\n    "))
    lines.append("")
    lines.append("When you need to use a tool, call it with the correct arguments as shown above. Always use the provided variable names.")
    return "\n".join(lines) + "\n"

# Standalone function for preparing the prompt

def prepare_prompt(config: NodeConfig, context_manager, llm_config: LLMConfig, tool_service, inputs: dict) -> str:
    template = config.prompt
    selected_contexts = {}
    # Filter inputs based on selection
    if config.input_selection:
        selected_contexts = {
            k: v for k, v in inputs.items() 
            if k in config.input_selection
        }
    else:
        selected_contexts = inputs
    # Apply context rules and format inputs
    formatted_inputs = {}
    for input_id, context in selected_contexts.items():
        rule = config.context_rules.get(input_id)
        if rule and rule.include:
            formatted_inputs[input_id] = context_manager.format_context(
                context,
                rule,
                config.format_specifications.get(input_id)
            )
        elif not rule or rule.include:
            formatted_inputs[input_id] = context
    # Add tool preamble if tools are available
    tools = None
    if config.tools:
        tools = [tool.model_dump() for tool in config.tools]
    else:
        tools = tool_service.list_tools_with_schemas() if tool_service else []
    preamble = build_tool_preamble(tools) if tools else ""
    # Build user message with all required input variables and their values
    user_lines = [template.strip()]
    if formatted_inputs:
        user_lines.append("\nInput variables:")
        for k, v in formatted_inputs.items():
            user_lines.append(f"{k}: {v}")
    user_message = "\n".join(user_lines)
    # Compose final prompt as system + user message
    prompt_with_preamble = preamble + user_message
    # Validate total token count
    try:
        total_tokens = TokenCounter.count_tokens(
            prompt_with_preamble,
            llm_config.model,
            llm_config.provider
        )
        # Only check token limits if max_context_tokens is set
        if llm_config.max_context_tokens is not None and total_tokens > llm_config.max_context_tokens:
            # Truncate prompt if needed
            prompt_with_preamble = prompt_with_preamble[:llm_config.max_context_tokens * 4]  # rough estimate
    except ValueError:
        pass
    return prompt_with_preamble 