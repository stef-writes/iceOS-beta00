import asyncio
import logging
import traceback
from typing import Any, Dict, Callable, Optional
from app.tools.base import BaseTool
from pydantic import ValidationError
from app.tools import CalculatorTool
from app.tools.transcript_parser import TranscriptParserTool
from app.tools.speaker_lister import SpeakerListerTool

logger = logging.getLogger(__name__)

class ToolExecutionError(Exception):
    pass

class ToolService:
    """
    Async service for tool discovery and invocation.
    Handles async/sync tools, error handling, timeouts, and structured results.
    """
    def __init__(self, timeout: float = 10.0):
        self.registry: Dict[str, BaseTool] = {}
        self.timeout = timeout

    def register_tool(self, tool: BaseTool):
        # Validate parameters_schema is a valid JSON Schema (type: object)
        schema = tool.get_parameters_json_schema()
        if not isinstance(schema, dict) or schema.get('type') != 'object':
            raise ValueError(f"Tool '{tool.name}' parameters_schema must be a valid JSON Schema object with type: 'object'.")
        self.registry[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def list_tools_with_schemas(self) -> list:
        """Return a list of all registered tools with their schemas and metadata."""
        tools = []
        for tool in self.registry.values():
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "parameters_schema": tool.get_parameters_json_schema(),
                "output_schema": tool.get_output_json_schema(),
                "usage_example": getattr(tool, "usage_example", None),
            })
        return tools

    async def execute(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name not in self.registry:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found.",
                "output": None,
                "tool_name": tool_name,
                "execution_time": 0.0
            }
        tool = self.registry[tool_name]
        start = asyncio.get_event_loop().time()
        try:
            # Validate parameters using the tool's Pydantic schema
            validated_params = tool.parameters_schema(**parameters)
            if asyncio.iscoroutinefunction(tool.run):
                coro = tool.run(**validated_params.dict())
            else:
                coro = asyncio.to_thread(tool.run, **validated_params.dict())
            result = await asyncio.wait_for(coro, timeout=self.timeout)
            success = True
            error = None
        except ValidationError as ve:
            result = None
            success = False
            error = f"Parameter validation failed: {ve}"
            logger.error(error)
        except Exception as e:
            result = None
            success = False
            error = f"Tool '{tool_name}' failed: {str(e)}"
            logger.error(error)
            logger.debug(traceback.format_exc())
        end = asyncio.get_event_loop().time()
        return {
            "success": success,
            "output": result,
            "error": error,
            "tool_name": tool_name,
            "execution_time": end - start
        }

    @staticmethod
    def register_default_tools(service: 'ToolService'):
        """Register all default/built-in tools."""
        service.register_tool(CalculatorTool())
        service.register_tool(TranscriptParserTool())
        service.register_tool(SpeakerListerTool())
