import os
import json
from src.app.chains.script_chain import ScriptChain
from src.app.models.node_models import NodeConfig, ToolConfig, NodeMetadata
from src.app.models.config import LLMConfig, ModelProvider
from src.app.utils.context import GraphContextManager
from src.app.services.tool_service import ToolService
from datetime import datetime, timedelta

# Load the transcript
with open('docs/mock-data/mock-transcript.txt', 'r') as f:
    transcript = f.read()

# Usage example for parser tool (makes LLM behavior deterministic)
parser_usage_example = (
    '{"function_call": {"name": "transcript_parser", "arguments": {"raw_transcript_text": "[00:00:01] Alice: Hello Bob!\\n[00:00:03] Bob: Hi Alice, how are you?"}}}'
)

# Usage example for speaker lister tool
speaker_usage_example = (
    '{"function_call": {"name": "speaker_lister", "arguments": {"utterances": [{"timestamp": "00:00:01", "speaker": "Alice", "text": "Hello Bob!"}]}}}'
)

# Set up ToolService and register default tools
tool_service = ToolService()
ToolService.register_default_tools(tool_service)

# Node 1: Transcript Parser (prompt is now extremely explicit)
parser_node = NodeConfig(
    id="parseme-1",
    type="ai",
    name="ParseMe",
    model="gpt-4",
    prompt=(
        "You must use the transcript_parser tool to process the following transcript.\n"
        "Example usage (always fill the argument):\n"
        f"{parser_usage_example}\n"
        "Now, call the tool with the provided transcript.\n"
        "Transcript:\n{raw_transcript_text}"
    ),
    dependencies=[],
    llm_config=LLMConfig(provider=ModelProvider.OPENAI, model="gpt-4"),
    tools=[ToolConfig(
        name="transcript_parser",
        description="Parses a raw transcript into a list of utterances with timestamp, speaker, and text.",
        usage_example=parser_usage_example
    )],
    input_schema={"raw_transcript_text": "str"},
    output_schema={"utterances": "list"},
    agentic=False
)

# Node 2: Speaker Lister (prompt is also explicit)
speaker_node = NodeConfig(
    id="speakerlist-1",
    type="ai",
    name="SpeakerLister",
    model="gpt-4",
    prompt=(
        "You must use the speaker_lister tool to process the utterances.\n"
        "Example usage (always fill the argument):\n"
        f"{speaker_usage_example}\n"
        "Now, call the tool with the provided utterances."
    ),
    dependencies=["parseme-1"],
    llm_config=LLMConfig(provider=ModelProvider.OPENAI, model="gpt-4"),
    tools=[ToolConfig(
        name="speaker_lister",
        description="Extracts a list of unique speakers from a list of utterances.",
        usage_example=speaker_usage_example
    )],
    input_schema={"utterances": "list"},
    output_schema={"speakers": "list"},
    agentic=False
)

# Patch realistic, complete metadata for both nodes
now = datetime.utcnow()
parser_node.metadata = NodeMetadata(
    node_id=parser_node.id,
    node_type=parser_node.type,
    name=parser_node.name,
    version="1.0.0",
    owner="test_user",
    created_at=now - timedelta(minutes=2),
    modified_at=now,
    description="Node that parses transcripts into utterances.",
    error_type=None,
    timestamp=now,
    start_time=now - timedelta(minutes=2),
    end_time=now - timedelta(minutes=1, seconds=30),
    duration=30.0,
    provider=parser_node.llm_config.provider
)
speaker_node.metadata = NodeMetadata(
    node_id=speaker_node.id,
    node_type=speaker_node.type,
    name=speaker_node.name,
    version="1.0.0",
    owner="test_user",
    created_at=now - timedelta(minutes=1, seconds=29),
    modified_at=now,
    description="Node that extracts speakers from utterances.",
    error_type=None,
    timestamp=now,
    start_time=now - timedelta(minutes=1, seconds=29),
    end_time=now - timedelta(minutes=1),
    duration=29.0,
    provider=speaker_node.llm_config.provider
)

# Set up the ScriptChain
nodes = [parser_node, speaker_node]
context_manager = GraphContextManager()
script_chain = ScriptChain(
    nodes=nodes,
    context_manager=context_manager,
    persist_intermediate_outputs=True,
    tool_service=tool_service
)

# Patch realistic, complete metadata for the chain
script_chain.chain_id = "test-chain-001"
script_chain.name = "Test Transcript Chain"
script_chain_metadata = NodeMetadata(
    node_id=script_chain.chain_id,
    node_type="script_chain",
    name=script_chain.name,
    version="1.0.0",
    owner="test_user",
    created_at=now - timedelta(minutes=3),
    modified_at=now,
    description="A test script chain for transcript parsing and speaker listing.",
    error_type=None,
    timestamp=now,
    start_time=now - timedelta(minutes=3),
    end_time=now,
    duration=180.0,
    provider=None
)
script_chain.metadata = script_chain_metadata

# Provide initial context for the parser node
context_manager.update_context("parseme-1", {"raw_transcript_text": transcript})

import asyncio

def default_serializer(obj):
    if isinstance(obj, (datetime, )):
        return obj.isoformat()
    return str(obj)

def print_documented_output(result):
    print("\n=== ScriptChain Execution Result ===\n")
    print(json.dumps(result.model_dump(exclude_none=True), indent=2, ensure_ascii=False, default=default_serializer))
    print("\n--- Node Outputs ---\n")
    for node_id, node_result in (result.output or {}).items():
        print(f"Node: {node_id}")
        print(json.dumps(node_result.model_dump(exclude_none=True), indent=2, ensure_ascii=False, default=default_serializer))
        print()
    print("\n--- Metadata ---\n")
    print(json.dumps(result.metadata.model_dump(exclude_none=True), indent=2, ensure_ascii=False, default=default_serializer))
    print("\n--- Token Stats ---\n")
    print(json.dumps(result.token_stats, indent=2, ensure_ascii=False, default=default_serializer))
    if result.error:
        print("\n--- Errors ---\n")
        print(result.error)

def main():
    try:
        result = asyncio.run(script_chain.execute())
        print_documented_output(result)

        # --- Automated assertions for CI ---
        # 1. The chain should succeed
        assert result.success, "ScriptChain did not succeed"

        # 2. Both nodes should succeed
        assert result.output["parseme-1"].success, "Parser node failed"
        assert result.output["speakerlist-1"].success, "Speaker lister node failed"

        # 3. The parser node should output a non-empty utterances list
        utterances = result.output["parseme-1"].output["utterances"]
        assert isinstance(utterances, list) and len(utterances) > 0, "No utterances parsed"

        # 4. The speaker lister node should output a non-empty speakers list
        speakers = result.output["speakerlist-1"].output["speakers"]
        assert isinstance(speakers, list) and len(speakers) > 0, "No speakers found"

        # 5. (Optional) Check for specific expected speakers
        expected_speakers = {"Alexander", "Dalio", "Turing", "Leonardo", "Zhuangzi"}
        found = expected_speakers.intersection(set([s.replace("**", "").replace(" ", "") for s in speakers]))
        assert found, f"Expected speakers not found in output: {speakers}"

        print("All assertions passed. Test succeeded.")

    except AssertionError as e:
        print(f"\n[ASSERTION FAILED] {e}")
        exit(1)
    except Exception as e:
        print("\n[ERROR] Exception during ScriptChain execution:")
        print(str(e))
        exit(1)

if __name__ == "__main__":
    main() 