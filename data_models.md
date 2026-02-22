# IsoMind Data Models & API Design (Draft)

## 1. Core Data Models (PostgreSQL + pgvector)

### `AgentProfiles`
Stores configuration for different agent instances.
- `id` (UUID, PK)
- `user_id` (UUID, FK)
- `name` (String) - e.g., "TikTok SMM Bot"
- `status` (Enum: STOPPED, RUNNING, ERROR)
- `vast_instance_id` (String) - ID of the rented container.
- `chromium_profile_path` (String) - Path to persistent session data in S3/EBS.
- `created_at` (Timestamp)

### `VisualAnchors` (Vector Database)
Stores the visual fragments used by the Semantic RAG system.
- `id` (UUID, PK)
- `blueprint_id` (UUID, FK)
- `semantic_label` (String) - e.g., "Post Button", "Email Input Field"
- `embedding` (Vector[1536]) - The generated vector representation of the visual crop.
- `bounding_box_relative` (JSON) - `{width_pct, height_pct}`
- `created_at` (Timestamp)

### `Blueprints`
Stores the recorded workflows.
- `id` (UUID, PK)
- `name` (String) - e.g., "Upload Video to TikTok"
- `state_graph` (JSONB) - The DAG representation of states and actions.

## 2. Internal Agent API (FastAPI inside Container)

This API runs *inside* the Sandbox and is called by the Platform Orchestrator or the LLM.

### `/v1/perception`
- **GET `/v1/perception/screenshot`**
  - **Returns:** Base64 encoded JPEG/PNG of the current Xvfb frame.
- **POST `/v1/perception/crop`**
  - **Payload:** `{ "x": 100, "y": 200, "width": 50, "height": 50 }`
  - **Returns:** Base64 crop of the specified region.

### `/v1/action`
- **POST `/v1/action/mouse/click`**
  - **Payload:** `{ "x": 500, "y": 600, "button": "left", "humanize": true }`
  - **Behavior:** Moves mouse using Bezier curves and clicks.
- **POST `/v1/action/keyboard/type`**
  - **Payload:** `{ "text": "Hello World", "delay_ms": 50 }`
- **POST `/v1/action/browser/navigate`**
  - **Payload:** `{ "url": "https://tiktok.com" }`

### `/v1/health`
- **GET `/v1/health/status`**
  - **Returns:** Status of Xvfb, Playwright, and local vLLM/Ollama nodes.
