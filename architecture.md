# IsoMind Architecture Specification

## 1. System Overview
IsoMind (Local-First AI Agentic Platform) utilizes a distributed architecture dividing the control plane (Platform Backend) and the execution plane (Isolated Agent Sandboxes on remote GPU instances).

## 2. Core Components

### 2.1 The Platform (Orchestrator)
- **Tech Stack:** Next.js (Frontend), FastAPI (Backend REST API), PostgreSQL + pgvector (Database).
- **Responsibilities:**
  - User authentication, multi-tenant data separation, and billing.
  - Provisioning and lifecycle management of compute resources via Vast.ai API.
  - Storing and serving "Task Blueprints" and "Visual RAG Vectors" (Memory).
  - WebRTC signal exchanges for the "Control Mirror".

### 2.2 The Sandbox (Agent Container)
- **Tech Stack:** Docker (Ubuntu + NVIDIA CUDA 12.x), Xvfb, Fluxbox/Openbox, Python 3.12, Chromium.
- **Inner Modules:**
  - **Display Server:** `Xvfb` creates the virtual screen (1920x1080).
  - **Browser & Automation Engine:** `Playwright` with Chromium.
  - **Local AI Engine:** `Ollama` or `vLLM` running locally within the container (Qwen 2.5-VL for vision reasoning, Moondream 2 for fast UI coordinate grounding).
  - **Stealth & Evasion Module:** Implements `playwright-stealth` to override browser fingerprints, manage proxies, and execute human-like Bezier-curve mouse movements.
  - **Visual Streamer:** `aiortc` or `selkies-gstreamer` to pipe the Xvfb frame buffer to the user's browser with sub-second latency.

### 2.3 Visual RAG (The Memory System)
- **Database:** PostgreSQL with `pgvector` extension.
- **Logic:** 
  - Instead of XPath/CSS selectors, UI elements are stored as visual embeddings. 
  - During the Teaching phase, a context patch (e.g., 100x100px) around a clicked element is processed by a Vision LLM to extract meaning, then embedded into a vector space.
  - During autonomous Execution, the agent searches the vector database to locate elements matching the semantic/visual profile, even if the DOM has changed.

### 2.4 Task Blueprints
- Workflows are defined as Directed Acyclic Graphs (DAGs) defined in JSON.
- **Nodes (States):** The semantic representation of the current screen ("Login Page").
- **Edges (Actions):** The actions required to transition out of the state ("Type Username, Press Enter").

## 3. Interaction & Communication Protocols
- **Backend $\leftrightarrow$ Sandbox:** Encrypted WebSocket or SSH tunneling for passing Blueprints, extracting logs, and requesting HitL (Human-in-the-loop) approvals.
- **Sandbox $\leftrightarrow$ User Browser:** WebRTC for high-fps, low-latency visual streaming during "Demonstration Mode" and Live Observation.
- **Sandbox $\leftrightarrow$ LLM:** Local HTTP REST over `localhost:11434` (OpenAI-compatible) to local Ollama/vLLM instances, ensuring zero external data leakage.

## 4. Pending Sub-system Designs
Several key technical mechanisms need further design decisions. These have been extracted to `questions.md` and include:
- Hardware limits for running heavy VLMs alongside automated browsers.
- Screen polling heuristics.
- Advanced object detection for UI elements.
- WebRTC NAT traversal logistics.
