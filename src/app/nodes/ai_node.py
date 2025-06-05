"""
Concrete node implementations using the data models
"""

import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union
from openai import AsyncOpenAI, OpenAI
from openai import APIError, RateLimitError, Timeout
import logging
import uuid
import asyncio
import json
import traceback
import re
from pydantic import ValidationError
from anthropic import AsyncAnthropic
import google.generativeai as genai

# Existing imports
# This is a test comment to trigger reload
from app.models.node_models import (
    NodeConfig, 
    NodeExecutionResult,
    NodeExecutionRecord,
    NodeMetadata,
    UsageMetadata,
    ContextRule
)
from app.models.config import LLMConfig, MessageTemplate, ModelProvider
from app.utils.context import GraphContextManager
from app.nodes.base import BaseNode
from app.utils.logging import logger
from app.utils.tracking import track_usage
from app.utils.callbacks import ScriptChainCallback
from app.utils.token_counter import TokenCounter
from app.llm_providers import OpenAIHandler, AnthropicHandler, GoogleGeminiHandler, DeepSeekHandler
from app.services.llm_service import LLMService
from app.services.tool_service import ToolService
from app.nodes.prompt_builder import build_tool_preamble, prepare_prompt, build_system_message_for_tool
from app.nodes.tool_call_utils import detect_tool_call, format_tool_output
from app.nodes.error_handling import OpenAIErrorHandler
from app.nodes.constants import TOOL_INSTRUCTION

logger = logging.getLogger(__name__)

class AiNode(BaseNode):
    """AI-powered node supporting LLM text generation and tool/function calling"""
    
    def __init__(
        self,
        config: NodeConfig,
        context_manager: GraphContextManager,
        llm_config: LLMConfig,
        callbacks: Optional[List[ScriptChainCallback]] = None,
        llm_service: Optional[LLMService] = None,
        tool_service: Optional[ToolService] = None
    ):
        """Initialize AI node with LLM and Tool services."""
        super().__init__(config)
        self.context_manager = context_manager
        self.llm_config = llm_config
        self.callbacks = callbacks or []
        self.llm_service = llm_service or LLMService()
        self.tool_service = tool_service or ToolService()
    
    def build_tool_preamble(self, tools: list) -> str:
        """Generate a human-readable preamble describing available tools, their parameters, and usage examples."""
        return build_tool_preamble(tools)

    async def prepare_prompt(self, inputs: Dict[str, Any]) -> str:
        """Prepare prompt with selected context from inputs, including a tool system message and preamble if tools are available."""
        # If this node uses tools, prepend a system message for the first tool (or all tools if needed)
        if self.config.tools:
            tool = self.config.tools[0].model_dump() if hasattr(self.config.tools[0], 'model_dump') else self.config.tools[0]
            system_msg = build_system_message_for_tool(tool)
        else:
            system_msg = ''
        user_prompt = prepare_prompt(self.config, self.context_manager, self.llm_config, self.tool_service, inputs)
        return (system_msg + '\n' + user_prompt).strip()

    def _truncate_prompt(self, prompt: str, current_tokens: int) -> str:
        """Truncate prompt to fit within token limit.
        
        Args:
            prompt: Prompt to truncate
            current_tokens: Current token count
            
        Returns:
            Truncated prompt
        """
        max_tokens = self.llm_config.max_context_tokens if self.llm_config.max_context_tokens is not None else 4096
        if current_tokens <= max_tokens:
            return prompt
        
        # Calculate how many tokens to remove
        tokens_to_remove = current_tokens - max_tokens
        
        # Estimate characters to remove (roughly 4 chars per token)
        chars_to_remove = tokens_to_remove * 4
        
        # Truncate from the end, preserving complete sentences
        truncated = prompt[:-chars_to_remove]
        last_period = truncated.rfind('.')
        if last_period > 0:
            truncated = truncated[:last_period + 1]
        
        return truncated

    def _prepare_messages(self, context: Optional[Dict] = None) -> List[Dict[str, str]]:
        """Prepare messages for the API call.
        
        Args:
            context: Optional context data
            
        Returns:
            List of message dictionaries
        """
        messages = []
        context = context or {}
        
        # Add system message if available
        if self.config.templates and "system" in self.config.templates:
            try:
                system_content = self.config.templates["system"].format(**context)
                messages.append({
                    "role": "system",
                    "content": system_content
                })
            except KeyError as e:
                logger.warning(f"Missing context key for system message: {e}")
        
        # Add user message
        try:
            user_content = self.config.prompt.format(**context)
            messages.append({
                "role": "user",
                "content": user_content
            })
        except KeyError as e:
            raise ValueError(f"Missing required context key: {e}")
        
        return messages

    def _build_tool_args_from_context(self, tool_name, tool_schema, context):
        """Build tool arguments from context and input_mappings, with error reporting."""
        tool_args = {}
        missing_args = []
        if tool_schema and 'properties' in tool_schema:
            for k in tool_schema['properties'].keys():
                # Use input_mappings if defined
                mapped = False
                if self.config.input_mappings and k in self.config.input_mappings:
                    mapping = self.config.input_mappings[k]
                    dep_context = self.context_manager.get_node_output(mapping.source_node_id)
                    value = dep_context.get(mapping.source_output_key)
                    if value is not None:
                        tool_args[k] = value
                        mapped = True
                if not mapped:
                    # Fallback: get from this node's context
                    if k in context:
                        tool_args[k] = context[k]
                    else:
                        missing_args.append(k)
        return tool_args, missing_args

    async def execute(self, context: Dict[str, Any] = None, max_steps: int = 5) -> NodeExecutionResult:
        """
        Execute the text generation node using the appropriate LLM service and handle tool/function calls.
        - If agentic is False: single-step deterministic tool call (or LLM output)
        - If agentic is True: agentic 'thought loop' (multi-step, tool-calling, iterative reasoning)
        """
        start_time = datetime.utcnow()
        context = context or {}
        error_message_prefix = f"Node '{self.config.id}' (Name: '{self.config.name}', Provider: {self.llm_config.provider}, Model: {self.llm_config.model}): "
        messages = []
        tool_outputs = []
        step = 0
        try:
            # Prepare the initial prompt (instructions only, no data)
            try:
                prompt_template_for_handler = await self.prepare_prompt({})  # Pass empty dict to avoid data in prompt
            except KeyError as e:
                logger.error(f"{error_message_prefix}Missing key '{str(e)}' for prompt template. Context: {json.dumps(context, indent=2, default=str)}", exc_info=True)
                return NodeExecutionResult(
                    success=False,
                    error=f"{error_message_prefix}Prompt formatting error: Missing key '{str(e)}'.",
                    metadata=self._create_error_metadata(start_time, "PromptFormattingError"),
                    execution_time=(datetime.utcnow() - start_time).total_seconds()
                )

            tools = self.tool_service.list_tools_with_schemas() if hasattr(self, 'tool_service') else []

            # --- Deterministic (single-step) mode ---
            if not self.config.agentic:
                generated_text, usage_dict, handler_error = await self.llm_service.generate(
                    llm_config=self.llm_config,
                    prompt=prompt_template_for_handler,
                    context={},  # No data in context for prompt
                    tools=tools
                )
                tool_name, _ = detect_tool_call(generated_text)
                # If this node is configured with a tool, always call the tool with context-derived arguments
                if self.config.tools and len(self.config.tools) > 0:
                    # If LLM didn't select a tool, default to the first tool
                    if not tool_name:
                        tool_name = self.config.tools[0].name
                    if tool_name.startswith("functions."):
                        tool_name = tool_name.split(".", 1)[1]
                    elif tool_name.startswith("tools."):
                        tool_name = tool_name.split(".", 1)[1]
                    logger.info(f"[DETERMINISTIC] Forcing tool/function call: {tool_name} (ignoring LLM args, using context)")
                    tool_schema = None
                    for t in tools:
                        if t['name'] == tool_name:
                            tool_schema = t.get('parameters_schema', {})
                            break
                    tool_args, missing_args = self._build_tool_args_from_context(tool_name, tool_schema, context)
                    if missing_args:
                        error_msg = f"Missing required tool arguments in context: {missing_args}"
                        logger.error(error_msg)
                        return NodeExecutionResult(
                            success=False,
                            output=None,
                            error=f"{error_message_prefix}{error_msg}",
                            metadata=self._create_error_metadata(start_time, "ToolArgumentError"),
                            execution_time=(datetime.utcnow() - start_time).total_seconds()
                        )
                    tool_exec_result = await self.tool_service.execute(tool_name, tool_args)
                    if tool_exec_result["success"]:
                        output = tool_exec_result["output"]
                        end_time = datetime.utcnow()
                        duration = (end_time - start_time).total_seconds()
                        return NodeExecutionResult(
                            success=True,
                            output=output,
                            error=None,
                            metadata=NodeMetadata(
                                node_id=self.config.id,
                                node_type=self.config.type,
                                version=self.config.metadata.version if self.config.metadata else "1.0.0",
                                start_time=start_time,
                                end_time=end_time,
                                duration=duration,
                                provider=self.config.provider
                            ),
                            usage=None,
                            execution_time=duration
                        )
                    else:
                        tool_error = tool_exec_result["error"]
                        end_time = datetime.utcnow()
                        duration = (end_time - start_time).total_seconds()
                        return NodeExecutionResult(
                            success=False,
                            output=None,
                            error=f"{error_message_prefix}{tool_error}" if tool_error else None,
                            metadata=NodeMetadata(
                                node_id=self.config.id,
                                node_type=self.config.type,
                                version=self.config.metadata.version if self.config.metadata else "1.0.0",
                                start_time=start_time,
                                end_time=end_time,
                                duration=duration,
                                provider=self.config.provider,
                                error_type="ToolExecutionError"
                            ),
                            usage=None,
                            execution_time=duration
                        )
                # If no tool is configured, fall back to validating LLM output
                output_data, validation_success, validation_error = self._process_and_validate_output(generated_text)
                final_success = validation_success
                final_error = validation_error if not validation_success else None
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()
                return NodeExecutionResult(
                    success=final_success,
                    output=output_data,
                    error=f"{error_message_prefix}{final_error}" if final_error else None,
                    metadata=NodeMetadata(
                        node_id=self.config.id,
                        node_type=self.config.type,
                        version=self.config.metadata.version if self.config.metadata else "1.0.0",
                        start_time=start_time,
                        end_time=end_time,
                        duration=duration,
                        provider=self.config.provider,
                        error_type="SchemaValidationError" if not final_success and validation_error else None
                    ),
                    usage=None,
                    execution_time=duration
                )

            # --- Agentic (multi-step) mode ---
            last_llm_output = None
            usage_metadata = None
            while step < max_steps:
                step += 1
                logger.debug(f"{error_message_prefix}Agentic loop step {step}")
                if step == 1:
                    llm_input = prompt_template_for_handler
                else:
                    tool_output_strs = [
                        format_tool_output(t['tool_name'], t['output']) for t in tool_outputs if t['success']
                    ]
                    llm_input = prompt_template_for_handler + "\n" + "\n".join(tool_output_strs)

                generated_text, usage_dict, handler_error = await self.llm_service.generate(
                    llm_config=self.llm_config,
                    prompt=llm_input,
                    context=context,
                    tools=tools
                )
                last_llm_output = generated_text

                tool_name, tool_args = detect_tool_call(generated_text)
                tool_call_detected = tool_name is not None
                tool_result = None
                tool_error = None

                if tool_call_detected:
                    if tool_name.startswith("functions."):
                        tool_name = tool_name.split(".", 1)[1]
                    elif tool_name.startswith("tools."):
                        tool_name = tool_name.split(".", 1)[1]
                    logger.info(f"Tool/function call detected: {tool_name} with args: {tool_args}")
                    tool_schema = None
                    for t in tools:
                        if t['name'] == tool_name:
                            tool_schema = t.get('parameters_schema', {})
                            break
                    # Always build tool_args from context, ignore LLM args
                    tool_args, missing_args = self._build_tool_args_from_context(tool_name, tool_schema, context)
                    if missing_args:
                        logger.warning(f"Tool call '{tool_name}' missing arguments. Attempting to auto-fill from context failed: {missing_args}")
                        continue  # Skip this tool call, go to next agentic step
                    tool_exec_result = await self.tool_service.execute(tool_name, tool_args)
                    tool_outputs.append(tool_exec_result)
                    if not tool_exec_result["success"]:
                        tool_error = tool_exec_result["error"]
                        end_time = datetime.utcnow()
                        duration = (end_time - start_time).total_seconds()
                        return NodeExecutionResult(
                            success=False,
                            output=None,
                            error=f"{error_message_prefix}{tool_error}" if tool_error else None,
                            metadata=NodeMetadata(
                                node_id=self.config.id,
                                node_type=self.config.type,
                                version=self.config.metadata.version if self.config.metadata else "1.0.0",
                                start_time=start_time,
                                end_time=end_time,
                                duration=duration,
                                provider=self.config.provider,
                                error_type="ToolExecutionError"
                            ),
                            usage=None,
                            execution_time=duration
                        )
                    # Continue the loop: send tool output back to LLM for further reasoning
                    continue
                if handler_error:
                    logger.error(f"{error_message_prefix}Handler error: {handler_error}")
                    return NodeExecutionResult(
                        success=False,
                        error=f"{error_message_prefix}{handler_error}",
                        metadata=self._create_error_metadata(start_time, "LLMHandlerError"),
                        execution_time=(datetime.utcnow() - start_time).total_seconds()
                    )
                output_data, validation_success, validation_error = self._process_and_validate_output(generated_text)
                final_success = validation_success
                final_error = validation_error if not validation_success else None
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()
                if usage_dict:
                    try:
                        usage_metadata = UsageMetadata(
                            prompt_tokens=usage_dict.get("prompt_tokens", 0),
                            completion_tokens=usage_dict.get("completion_tokens", 0),
                            total_tokens=usage_dict.get("total_tokens", 0),
                            model=self.llm_config.model,
                            node_id=self.config.id,
                            provider=self.config.provider
                        )
                    except Exception as e_usage:
                        logger.error(f"{error_message_prefix}Failed to create UsageMetadata: {str(e_usage)}", exc_info=True)
                return NodeExecutionResult(
                    success=final_success,
                    output=output_data,
                    error=f"{error_message_prefix}{final_error}" if final_error else None,
                    metadata=NodeMetadata(
                        node_id=self.config.id,
                        node_type=self.config.type,
                        version=self.config.metadata.version if self.config.metadata else "1.0.0",
                        start_time=start_time,
                        end_time=end_time,
                        duration=duration,
                        provider=self.config.provider,
                        error_type="SchemaValidationError" if not final_success and validation_error else None
                    ),
                    usage=usage_metadata,
                    execution_time=duration
                )
            logger.warning(f"{error_message_prefix}Max agentic steps ({max_steps}) reached.")
            return NodeExecutionResult(
                success=False,
                output=None,
                error=f"{error_message_prefix}Max agentic steps ({max_steps}) reached.",
                metadata=self._create_error_metadata(start_time, "MaxStepsReached"),
                execution_time=(datetime.utcnow() - start_time).total_seconds()
            )
        except Exception as e:
            logger.error(f"{error_message_prefix}Unexpected error in execute method: {str(e)}", exc_info=True)
            return NodeExecutionResult(
                success=False,
                error=f"{error_message_prefix}Execution Error: {str(e)}",
                metadata=self._create_error_metadata(start_time, e.__class__.__name__),
                execution_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """Validate input data against schema.
        
        Args:
            inputs: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not self.config.input_schema:
            return True
            
        for key, expected_type in self.config.input_schema.items():
            if key not in inputs:
                return False
            if not isinstance(inputs[key], eval(expected_type)):
                return False
        return True
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """Calculate the cost of the API call.
        
        Args:
            usage: Token usage data
            
        Returns:
            Cost in USD
        """
        # TODO: Implement cost calculation based on model and provider
        return 0.0
    
    @property
    def input_keys(self) -> List[str]:
        """Get list of input keys."""
        return list(self.config.input_schema.keys()) if self.config.input_schema else []
    
    @property
    def output_keys(self) -> List[str]:
        """Get list of output keys."""
        return list(self.config.output_schema.keys()) if self.config.output_schema else []
    
    def get_template(self, role: str) -> MessageTemplate:
        """Get message template for a role.
        
        Args:
            role: Message role
            
        Returns:
            MessageTemplate object
        """
        if not self.config.templates or role not in self.config.templates:
            return None
        return self.config.templates[role]
    
    def _build_messages(self, inputs: Dict, context: Dict) -> List[Dict]:
        """Build message list for API call.
        
        Args:
            inputs: Input data
            context: Context data
            
        Returns:
            List of message dictionaries
        """
        messages = []
        
        # Add system message if available
        system_template = self.get_template("system")
        if system_template:
            messages.append({
                "role": "system",
                "content": system_template.format(**context)
            })
        
        # Add user message
        user_template = self.get_template("user")
        if user_template:
            messages.append({
                "role": "user",
                "content": user_template.format(**inputs)
            })
        else:
            messages.append({
                "role": "user",
                "content": self.config.prompt.format(**inputs)
            })
        
        return messages
    
    def _truncate_messages(self, messages: List[Dict], current_tokens: int) -> List[Dict]:
        """Truncate messages to fit token limit.
        
        Args:
            messages: List of message dictionaries
            current_tokens: Current token count
            
        Returns:
            Truncated list of messages
        """
        if current_tokens <= self.llm_config.max_context_tokens:
            return messages
            
        # Remove oldest messages first
        while current_tokens > self.llm_config.max_context_tokens and len(messages) > 1:
            removed = messages.pop(0)
            try:
                removed_tokens = TokenCounter.count_tokens(
                    removed["content"],
                    self.llm_config.model,
                    self.llm_config.provider
                )
                current_tokens -= removed_tokens
            except ValueError:
                # If we can't count tokens, estimate
                current_tokens -= len(removed["content"]) // 4
                
        return messages
    
    def _process_response(self, response: Dict) -> Tuple[str, UsageMetadata]:
        """Process API response.
        
        Args:
            response: API response
            
        Returns:
            Tuple of (text, usage_metadata)
        """
        text_content = response.choices[0].message.content
        text = text_content.strip() if text_content else ""
        usage = UsageMetadata(
            model=self.llm_config.model,
            node_id=self.config.id,
            provider=self.llm_config.provider,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens
        )
        return text, usage
    
    def _format_error(self, error: Exception) -> str:
        """Format error message."""
        return OpenAIErrorHandler.format_error_message(error)
    
    def _update_execution_stats(self, result: NodeExecutionResult):
        """Update execution statistics."""
        if result.usage:
            self.metrics["total_tokens"] += result.usage["total_tokens"]
            self.metrics["token_usage"][self.llm_config.provider] = result.usage

    def _create_error_metadata(self, start_time: datetime, error_type_str: str) -> NodeMetadata:
        """Helper to create metadata for error results."""
        return NodeMetadata(
            node_id=self.config.id,
            node_type=self.config.type,
            version=self.config.metadata.version if self.config.metadata else "1.0.0",
            start_time=start_time,
            end_time=datetime.utcnow(),
            duration=(datetime.utcnow() - start_time).total_seconds(),
            error_type=error_type_str,
            provider=self.config.provider
        )

    def _process_and_validate_output(self, generated_text: str) -> Tuple[Dict[str, Any], bool, Optional[str]]:
        """Processes the raw text from LLM and validates against output_schema.
        Robustly handles function_call wrappers, stringified JSON, and schema validation for any node.
        """
        logger.debug(f"[_PVP] Raw generated_text: '{generated_text}'")
        output = None
        error = None

        def try_parse_json(val):
            try:
                return json.loads(val)
            except Exception:
                return None

        # Step 1: Try direct JSON
        parsed = try_parse_json(generated_text.strip())

        # Step 2: If function_call wrapper, extract arguments
        if isinstance(parsed, dict) and "function_call" in parsed:
            call = parsed["function_call"]
            args = call.get("arguments")
            if isinstance(args, str):
                parsed = try_parse_json(args)
            elif isinstance(args, dict):
                parsed = args

        # Step 3: If still a string, try parsing again
        if isinstance(parsed, str):
            parsed = try_parse_json(parsed)

        # Step 4: If still not a dict, fallback to empty dict
        if not isinstance(parsed, dict):
            parsed = {}

        output = parsed

        # Step 5: Validate against output_schema
        if self.config.output_schema:
            for key, expected_type in self.config.output_schema.items():
                if key not in output:
                    return {}, False, f"Output schema validation failed: Missing key '{key}' (expected type '{expected_type}')"
                value = output[key]
                try:
                    if expected_type == "list":
                        if not isinstance(value, list):
                            # Try to parse as JSON list if it's a string
                            if isinstance(value, str):
                                value = try_parse_json(value)
                            if not isinstance(value, list):
                                return {}, False, f"Output schema validation failed: '{key}' is not a valid JSON list"
                        # If this is the utterances field, check structure
                        if key == "utterances":
                            for i, item in enumerate(value):
                                if not isinstance(item, dict) or not all(k in item for k in ("timestamp", "speaker", "text")):
                                    return {}, False, f"Output schema validation failed: Item {i} in '{key}' is not a valid utterance dict"
                        output[key] = value
                    elif expected_type == "str":
                        if not isinstance(value, str):
                            value = str(value)
                        output[key] = value
                    elif expected_type == "int":
                        if not isinstance(value, int):
                            value = int(value)
                        output[key] = value
                    elif expected_type == "float":
                        if not isinstance(value, (int, float)):
                            value = float(value)
                        output[key] = value
                    else:
                        output[key] = value
                except (ValueError, TypeError) as e:
                    return {}, False, f"Output schema validation failed: Cannot convert '{output[key]}' to {expected_type} for key '{key}': {str(e)}"
        logger.debug(f"[_PVP] Final output: {output}")
        return output, True, None