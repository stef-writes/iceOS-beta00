# ScriptChain Data Schemas

This folder contains JSON Schemas and example configurations for multi-provider, multi-level ScriptChain workflows.

**Note:** Only `AiNode` is supported as a node type. All tool/function calling is handled via the `agentic` flag (for multi-step vs. single-step behavior) and backend-injected tool schemas. There are no other node types at this time.

- `node_config.schema.json`: Node configuration schema
- `node_metadata.schema.json`: Node metadata schema
- `script_chain.schema.json`: ScriptChain configuration schema
- `script_chain_metadata.schema.json`: ScriptChain metadata schema
- `example_many_to_one.json`: Example of many-to-one multi-provider workflow
- `example_one_to_many.json`: Example of one-to-many multi-provider workflow

All schemas are compatible with the ScriptChain 3.0 architecture. 