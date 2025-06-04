# iceOS Engineering Roadmap (Beta01+)

_This roadmap is a living, in-depth reference for the technical evolution of iceOS. It is designed for engineering teams and technical stakeholders, and is tightly aligned with the platform's strategy, vision, and current implementation. Each section references the present state, next steps, and how it fits the overall business and product goals._

---

## 1. Core Platform Foundations

### 1.1. Configuration & Environment
- **Current State:** Basic config via `.env` and some hardcoded values. No unified settings class.
- **Next Steps:**
  - Centralize all configuration in a Pydantic `Settings` class.
  - Move all secrets and environment-specific values to `.env` files.
  - Support YAML/JSON config for non-secret settings.
  - Validate and log configuration (excluding secrets) at startup.
  - Implement feature flags for experimental features.
- **Strategic Fit:** Enables multi-environment deployments, security, and operational clarity.

### 1.2. Modularity & Service Architecture
- **Current State:** Modular services for LLM, tools, context, etc. Dependency injection is partial.
- **Next Steps:**
  - Refactor all services for full dependency injection.
  - Define clear interfaces for all core services.
  - Ensure all services are injectable and testable.
- **Strategic Fit:** Foundation for extensibility, testing, and plugin ecosystem.

### 1.3. Extensibility & Plugins
- [ ] Design and implement a plugin system for nodes, tools, agents, and chains.
- [ ] Provide APIs for third-party extension registration.
- [ ] Support integration adapters (LangChain, LlamaIndex, CrewAI, etc.).
- [ ] Document plugin development and integration.

---

## 2. Node & Chain System

### 2.1. Node Abstraction & Generalization
- **Current State:**
  - `BaseNode` and `AiNode` implemented. Node factory exists for `AiNode`.
  - Agentic node type planned but not yet implemented.
- **Next Steps:**
  - Implement `AgenticNode` (autonomous, planning-capable, multi-step).
  - Update node factory to support both node types.
  - Standardize node input/output schemas and metadata.
  - Specialized nodes (OCR, embedding, etc.) should be wrappers, ready to be replaced by general AI or agentic nodes as LLMs advance.
- **Strategic Fit:** Core to platform flexibility, future-proofing, and agentic workflows.

### 2.2. ScriptChain Orchestration
- **Current State:**
  - `ScriptChain` supports parallel execution, dependency management, and context.
- **Next Steps:**
  - Add support for both node types in orchestration.
  - Implement ScriptChain-to-ScriptChain communication protocol (for distributed workflows).
  - Add metrics, error reporting, and callbacks.
- **Strategic Fit:** Enables robust, scalable, and observable workflow execution.

### 2.3. Observability & Evaluation
- **Current State:**
  - Some metrics and error handling in backend.
- **Next Steps:**
  - Implement structured logging (JSON).
  - Add distributed tracing (OpenTelemetry).
  - Build metrics dashboards (Grafana, etc.).
  - Integrate built-in evaluation for chains and nodes (quality, performance).
- **Strategic Fit:** Critical for reliability, debugging, and enterprise adoption.

---

## 3. Visual Workflow Builder (Canvas UI)

### 3.1. Drag-and-Drop Editor
- **Current State:** Not present; planned in roadmap.
- **Next Steps:**
  - Build drag-and-drop canvas for node/chain construction.
  - Node/chain/flow config panels (schema-driven).
  - Support both AI Nodes and Agentic Nodes as distinct, selectable node types.
  - Enable real-time validation and feedback.
- **Strategic Fit:** Key to no-code/low-code accessibility and rapid prototyping.

### 3.2. Execution Visualization
- **Current State:** Not present.
- **Next Steps:**
  - Visualize execution flow, status, and errors on the canvas.
  - Allow step-through debugging and inspection of node outputs.
  - Visualize agentic node plans, memory, and tool use traces.
- **Strategic Fit:** Essential for transparency, debugging, and user trust.

### 3.3. Extensibility
- **Current State:** Not present.
- **Next Steps:**
  - Allow users to add custom nodes/tools/agents via UI or plugin upload.
  - Support import/export of workflows (JSON/YAML).
- **Strategic Fit:** Drives ecosystem growth and user empowerment.

---

## 4. Frosty Copilot: Natural Language Workflow Builder

### 4.1. Prompt-to-Workflow
- **Current State:** Spec and conceptual requirements are well-documented. No code implementation yet.
- **Next Steps:**
  - Implement prompt-to-network/flow/chain/node generation.
  - Copilot panel for NL interaction, explanations, and suggestions.
  - Real-time feedback and debugging help.
  - Round-trip editing (canvas <-> prompt).
- **Strategic Fit:** Core differentiator for accessibility and user onboarding.

### 4.2. Iterative Refinement
- [ ] Users can edit the workflow via prompt or UI.
- [ ] Frosty updates the architecture, explains changes, and offers debugging help.
- [ ] Frosty can recommend when to use agentic nodes for more autonomy or AI nodes for determinism.

### 4.3. Round-Trip Editing
- [ ] Support "canvas to prompt" and "prompt to canvas" round-tripping.
- [ ] Frosty can answer "why" and "how" questions about the workflow, including node type trade-offs.

### 4.4. Learning & Feedback
- [ ] Frosty learns from user edits and feedback to improve suggestions.
- [ ] Integrate user feedback loop for Copilot improvement.

---

## 5. Plugin System & Extensibility
- **Current State:** Plugin system is in roadmap, not yet implemented.
- **Next Steps:**
  - Design and implement plugin system for nodes, tools, agents, and chains.
  - Provide APIs for third-party extension registration.
  - Support integration adapters (LangChain, LlamaIndex, CrewAI, etc.).
  - Document plugin development and integration.
- **Strategic Fit:** Enables a thriving ecosystem and marketplace.

---

## 6. Marketplace & Sharing
- **Current State:** Not present.
- **Next Steps:**
  - Build marketplace UI and backend (browse, install, share, purchase).
  - Export/import (JSON/YAML) for networks, flows, chains, nodes.
  - Usage tracking and billing logic.
- **Strategic Fit:** Monetization, community growth, and network effects.

---

## 7. Automation, File Watcher, and Triggers
- **Current State:** Not present.
- **Next Steps:**
  - Implement file watcher node (e.g., using `watchdog`).
  - Automation triggers and scheduling.
- **Strategic Fit:** Enables end-to-end automation and real-world integrations.

---

## 8. Documentation & Templates
- **Current State:** Docs and templates are in progress; onboarding is in docs only.
- **Next Steps:**
  - Guided onboarding flow for new users.
  - Example templates (Zoom Q&A, sales analysis, etc.).
  - In-app documentation and troubleshooting.
- **Strategic Fit:** Lowers barrier to entry and accelerates adoption.

---

## 9. Security, Testing, and Quality
- **Current State:** Security and testing are basic; no dedicated modules.
- **Next Steps:**
  - Authentication and authorization for all APIs and user actions.
  - Input validation and audit logging.
  - Unit, integration, and end-to-end tests for all modules and workflows.
  - Property-based testing for node/chain logic.
- **Strategic Fit:** Required for enterprise, compliance, and reliability.

---

## 10. Performance & Scalability
- **Current State:** Not present.
- **Next Steps:**
  - Caching for expensive operations.
  - Asynchronous processing and horizontal scaling.
- **Strategic Fit:** Supports growth, cost control, and user experience.

---

## 11. Cross-References
- See [STRATEGY.md] for business context and competitive positioning.
- See [SPRINT_PLAN.md] for sprint-by-sprint execution plan.
- See [FROSTY_COPILOT.md] for Copilot technical/product spec.
- See [ZOOM_QA_NETWORK_EXAMPLE.md] for a comprehensive use case.

---

## Appendix: Toward Full Specification

### A. Agentic Node Technical Design
- **Current State:** Agentic node concept is specified, but implementation is pending. Planning, memory, and tool interfaces are not yet formalized.
- **Next Steps:**
  - Define agentic node lifecycle (goal intake, planning, execution, memory read/write, tool invocation).
  - Specify memory interface (short-term, long-term, context window management).
  - Standardize tool interface (schema, invocation, error handling).
  - Implement debugging hooks (plan trace, tool call logs, memory snapshots).
- **Fully Specified:** Detailed class diagrams, lifecycle sequence diagrams, and API docs for agentic node planning, memory, and tool use. Debugging UI and logs for agentic execution.

### B. Plugin System APIs and Lifecycle
- **Current State:** Plugin system is in the roadmap, not yet implemented. No formal API or lifecycle.
- **Next Steps:**
  - Define plugin registration, loading, and sandboxing APIs.
  - Specify plugin lifecycle (install, activate, update, deactivate, remove).
  - Document extension points (nodes, tools, chains, UI components).
- **Fully Specified:** Versioned plugin API docs, lifecycle diagrams, and security model for plugin execution.

### C. Visual Builder Data Model and Extensibility
- **Current State:** Visual builder is in design; data model is not finalized.
- **Next Steps:**
  - Define canonical data model for networks, flows, chains, nodes, and connections.
  - Specify schema for custom node types, UI extensions, and plugin-injected components.
- **Fully Specified:** Data model diagrams, JSON schema, and extension API docs for the visual builder.

### D. Security Model for User Code/Plugins
- **Current State:** Security model is not yet implemented; only basic input validation.
- **Next Steps:**
  - Define sandboxing and permission model for user code/plugins.
  - Specify audit logging and monitoring for plugin actions.
- **Fully Specified:** Security policy docs, sandboxing implementation, and compliance checklists for user-contributed code.

### E. Marketplace Asset Validation/Versioning
- **Current State:** Marketplace is in design; no asset validation or versioning implemented.
- **Next Steps:**
  - Define validation pipeline for submitted assets (linting, schema checks, security scan).
  - Specify versioning scheme for assets (semantic versioning, compatibility checks).
- **Fully Specified:** Asset validation workflow, versioning policy, and rollback/upgrade procedures.

### F. Testing/CI/CD Details
- **Current State:** Basic unit/integration tests; no formal CI/CD pipeline.
- **Next Steps:**
  - Implement CI/CD pipeline (build, test, lint, deploy).
  - Define test coverage requirements and reporting.
- **Fully Specified:** CI/CD pipeline diagrams, test matrix, and quality gates for all major subsystems.

---

_These areas are the focus for moving from "crystal clear" to "fully specified" and will be expanded as the platform matures._

---

_This roadmap is updated as the platform evolves. For questions or contributions, contact the core engineering team._
