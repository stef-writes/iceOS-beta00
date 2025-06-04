# Zoom Q&A Chat Assistant: Network, Flows, Chains, and Nodes

## Overview
This document details how to architect the "Zoom Q&A Chat Assistant" in iceOS using the Network → Flow → Chain → Node paradigm. It includes technical specifics, user experience guidance, and best practices for balancing agentic and deterministic nodes.

---

## 1. Network Structure

### Network: **Zoom Q&A Chat Assistant**
- **Description:** End-to-end automation for ingesting Zoom sessions and enabling intelligent Q&A.
- **Includes:** Multiple Flows, each representing a major stage of the pipeline.

---

## 2. Flows, Chains, and Nodes

### Flow 1: **Ingestion & Preprocessing Flow**
- **Description:** Handles all data collection and extraction from Zoom assets.

  - **Chain 1: Zoom Asset Collection Chain**
    - **Node 1:**
      - Name: ZoomIngestionNode
      - Description: Detects new Zoom recordings (API/webhook/file watcher)
      - Type: AiNode
      - Includes: Zoom API, file watcher
    - **Node 2:**
      - Name: AssetCollectorNode
      - Description: Collects all session files (.mp4, .m4a, chat.txt, whiteboard.png)
      - Type: AiNode
      - Includes: File system, metadata extraction

  - **Chain 2: Transcription Chain**
    - **Node 1:**
      - Name: TranscriptionNode
      - Description: Transcribes audio/video using Whisper
      - Type: AiNode
      - Includes: Whisper API, diarization option
    - **Node 2:**
      - Name: SpeakerDiarizationNode
      - Description: Identifies speakers in transcript
      - Type: AiNode
      - Includes: PyAnnote, WhisperX

  - **Chain 3: Chat Parsing Chain**
    - **Node 1:**
      - Name: ChatParserNode
      - Description: Parses chat logs into structured JSON
      - Type: AiNode
      - Includes: Regex, timestamp alignment

  - **Chain 4: Visual Extraction Chain**
    - **Node 1:**
      - Name: FrameSamplerNode
      - Description: Samples frames from video
      - Type: AiNode
      - Includes: ffmpeg, frame interval config
    - **Node 2:**
      - Name: OCRNode
      - Description: Extracts text from frames
      - Type: AiNode
      - Includes: Tesseract, PaddleOCR
    - **Node 3:**
      - Name: WhiteboardParserNode
      - Description: Parses whiteboard images (YOLOv8, OpenCV, OCR)
      - Type: AiNode
      - Includes: YOLOv8, OpenCV, OCR

---

### Flow 2: **Chunking & Structuring Flow**
- **Description:** Segments and links all extracted data.

  - **Chain 1: Chunking Chain**
    - **Node 1:**
      - Name: ChunkerNode
      - Description: Segments transcript and chat into semantic chunks
      - Type: AiNode
      - Includes: NLTK, spaCy, topic modeling
    - **Node 2:**
      - Name: LinkerNode
      - Description: Links chat, transcript, and visuals by timestamp
      - Type: AiNode
      - Includes: Timestamp alignment logic

---

### Flow 3: **Embedding & Indexing Flow**
- **Description:** Embeds and stores all chunks for retrieval.

  - **Chain 1: Embedding Chain**
    - **Node 1:**
      - Name: EmbedderNode
      - Description: Embeds text and diagrams
      - Type: AiNode
      - Includes: OpenAI, HuggingFace, CLIP
    - **Node 2:**
      - Name: IndexerNode
      - Description: Stores vectors and metadata
      - Type: AiNode
      - Includes: Chroma, FAISS, Pinecone, Postgres

---

### Flow 4: **Knowledge Enhancement Flow** (Optional)
- **Description:** Extracts entities/relations and builds a knowledge graph.

  - **Chain 1: Knowledge Graph Chain**
    - **Node 1:**
      - Name: NERNode
      - Description: Named entity recognition
      - Type: AiNode
      - Includes: spaCy, LLM
    - **Node 2:**
      - Name: RelationExtractionNode
      - Description: Extracts relationships
      - Type: AiNode
      - Includes: OpenIE, LLM
    - **Node 3:**
      - Name: GraphBuilderNode
      - Description: Builds and stores knowledge graph
      - Type: AiNode
      - Includes: Neo4j, JSON triples

---

### Flow 5: **Q&A Chatbot Flow**
- **Description:** Handles user queries and generates answers.

  - **Chain 1: RAG Chatbot Chain**
    - **Node 1:**
      - Name: QueryEmbedderNode
      - Description: Embeds user queries
      - Type: AiNode
      - Includes: OpenAI, HuggingFace
    - **Node 2:**
      - Name: RetrieverNode
      - Description: Retrieves top-k relevant chunks
      - Type: AiNode
      - Includes: Vector DB, filters
    - **Node 3:**
      - Name: RAGAgentNode
      - Description: Plans, reasons, and generates answers using retrieved context (multi-step, tool use, memory)
      - Type: Agentic AiNode
      - Includes: LLM, tool calling, memory, references
    - **Node 4:**
      - Name: ReferenceFormatterNode
      - Description: Formats answer with references
      - Type: AiNode
      - Includes: Formatting logic

---

### Flow 6: **Frontend & Automation Flow**
- **Description:** Connects backend to UI and automates the pipeline.

  - **Chain 1: Frontend Chain**
    - **Node 1:**
      - Name: ChatInterfaceNode
      - Description: User chat interface
      - Type: AiNode
      - Includes: Web UI, API connection
    - **Node 2:**
      - Name: SearchFilterNode
      - Description: UI for filtering/search
      - Type: AiNode
      - Includes: UI logic
    - **Node 3:**
      - Name: TimelineNode
      - Description: Visualizes session timeline
      - Type: AiNode
      - Includes: Timeline UI
    - **Node 4:**
      - Name: VisualPopupNode
      - Description: Displays visuals/whiteboards
      - Type: AiNode
      - Includes: UI logic

  - **Chain 2: Automation Chain**
    - **Node 1:**
      - Name: FileWatcherNode
      - Description: Watches for new Zoom files
      - Type: AiNode
      - Includes: Watchdog, triggers

---

## 3. User Experience: Building the Network

### Step 1: Start with Frosty Copilot
- User describes the workflow in natural language (e.g., "I want to analyze Zoom calls and build a Q&A chatbot").
- Frosty generates a draft network with flows, chains, and nodes on the canvas, recommending AI or Agentic nodes as appropriate.

### Step 2: Refine in the Visual Builder
- User reviews the generated structure.
- User can drag, drop, and connect nodes, edit node types (AI vs. Agentic), and configure node settings (e.g., select Whisper for transcription, OpenAI for embedding).
- Frosty provides real-time feedback, explains node type trade-offs, and suggests optimizations.

### Step 3: In-Node Work
- For advanced customization, user can open any node to:
  - Edit prompts, tool schemas, or agentic planning logic.
  - Add or remove tools for agentic nodes.
  - Set memory or context options.
- Frosty can assist with in-node configuration and debugging.

### Step 4: Test and Debug
- User runs the pipeline on a sample Zoom session.
- Step-through debugging and output inspection are available for each node.
- For agentic nodes, the user can view the plan, memory, and tool use trace.
- Frosty helps interpret errors and suggests fixes, especially for non-technical users.

### Step 5: Deploy and Iterate
- User activates the automation loop (e.g., file watcher triggers full pipeline).
- Users interact with the chatbot via the frontend UI.
- User can iterate, add new nodes, or switch node types as needs evolve.

---

## 4. Agentic Node Reusability, Reruns, and Debugging

### Reusability
- **Best Practice:** Design agentic nodes to accept clear, well-defined goals and expose their toolset and memory interfaces.
- **Tip:** Where possible, break complex agentic logic into smaller, composable agentic or AI nodes for easier reuse.

### Reruns
- **Challenge:** Agentic nodes may have non-deterministic outputs due to planning, tool use, or memory.
- **Solution:**
  - Allow users to snapshot agentic node state and plans for reproducibility.
  - Provide options to run agentic nodes in a "deterministic mode" (fixed plan, no memory) for testing.

### Debugging for Non-Technical Users
- **Frosty Copilot:**
  - Explains errors in plain language.
  - Suggests fixes or alternative node types.
  - Can auto-generate test cases and walk users through debugging steps.
- **Visual Builder:**
  - Step-through execution and output inspection for all nodes.
  - Visualizes agentic node plans and memory.
- **Documentation:**
  - Each node type includes a "Troubleshooting" section with common issues and solutions.

---

## 5. Summary Table

| Level     | Name/Type         | Description/Includes                                 |
|-----------|-------------------|-----------------------------------------------------|
| Network   | Zoom Q&A Chat Assistant | End-to-end automation for Zoom session Q&A      |
| Flow      | Ingestion & Preprocessing | Data collection and extraction                |
| Chain     | Transcription Chain | Transcribes audio/video, diarization               |
| Node      | TranscriptionNode (AiNode) | Whisper API, deterministic                    |
| Node      | RAGAgentNode (Agentic AiNode) | LLM, tool use, memory, multi-step reasoning |

---

## 6. Best Practices
- Use AI Nodes for deterministic, well-defined tasks (transcription, embedding, parsing).
- Use Agentic Nodes for open-ended, multi-step, or tool-using tasks (complex Q&A, research, knowledge graph building).
- Leverage Frosty Copilot for guidance, debugging, and optimization at every step.
- Design for modularity and composability to maximize reusability and maintainability. 