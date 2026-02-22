# IsoMind Requirements Specification (Phase 1)

## 1. User Stories (MVP Scope)
- **As a Developer/User**, I want to rent a GPU proxy container on Vast.ai so that my agent has a dedicated, isolated environment to operate in without polluting my local machine.
- **As a Developer/User**, I want to see the agent's screen in real-time through my browser so that I can observe its actions and intervene if necessary.
- **As an Agent**, I need to be able to click, type, and scroll within a standard web browser so that I can interact with modern web applications (SPA/React).
- **As an Agent**, I need to capture fragments of the screen and convert them to vector embeddings so that I can recognize UI elements even if their DOM structure changes.
- **As a User**, I want to demonstrate a task (blueprint) to the agent by manually clicking through a workflow while the system records the visual anchors and creates a JSON state machine.

## 2. Non-Functional Requirements (NFRs)
- **Latency:** The visual streaming feed (WebRTC/noVNC) must operate with $< 500ms$ glass-to-glass latency to allow for comfortable human demonstration and intervention.
- **Isolation:** The Docker container must NOT mount the host OS filesystem. It should only have access to specific volumes (e.g., Chromium User Data Dir).
- **Stealth:** The Chromium instance must score $> 90\%$ on standard bot-detection tests (e.g., cloudflare turnstile, bot.sannysoft.com) to ensure it is not immediately blocked by target platforms.
- **Scalability:** The architecture must allow multiple isolated Agent containers to run concurrently on a single high-VRAM GPU (e.g., RTX 4090) if the Vision Model is shared.

## 3. Assumptions & Constraints
- **Hardware:** Target deployment environments are consumer-grade NVIDIA GPUs (RTX 3090, 4090, A6000) available on Vast.ai. AMD GPUs are out of initial scope.
- **OS:** Host machines run Ubuntu Linux. The container base image will be Ubuntu 22.04 with CUDA 12.1.
- **Browser:** Only Chromium (via Playwright) will be supported initially. Firefox/WebKit are excluded to reduce complexity in the stealth layer.
