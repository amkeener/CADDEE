---
status: done
type: feature
complexity: major
expert: caddee-sidecar
secondary_experts:
  - caddee-electron
  - caddee-ipc
---

# Plan: Phase 4 — Image Input

## Task Description
Add image/sketch upload to the chat console. Users can attach photos, sketches, or technical drawings, and Claude's vision capabilities extract dimensional intent to generate an initial .scad starting point.

## Objective
Enable visual-to-CAD workflows. Users photograph a physical object, sketch on paper, or screenshot a technical drawing, and CADDEE uses Claude's multimodal vision to interpret it and generate parametric OpenSCAD code.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Electron Renderer                                              │
│  ┌───────────┐ ┌────────────────────────────┐ ┌─────────────┐  │
│  │ Viewport  │ │  Chat Console              │ │ Tools Panel │  │
│  │           │ │  ├─ Image upload button [NEW]│ │             │  │
│  │           │ │  ├─ Drag-and-drop [NEW]     │ │             │  │
│  │           │ │  ├─ Clipboard paste [NEW]   │ │             │  │
│  │           │ │  └─ Image preview strip [NEW]│ │             │  │
│  └───────────┘ └────────────────────────────┘ └─────────────┘  │
└─────────────────────────────────────────────────────────────────┘
        ↕ IPC (images as data URLs in existing ChatRequest.images)
┌─────────────────────────────────────────────────────────────────┐
│  Python Sidecar                                                 │
│  ├─ claude_service.py [MODIFIED — multimodal content blocks]    │
│  ├─ main.py [MODIFIED — pass images to Claude]                  │
│  └─ prompts/system_prompt.txt [MODIFIED — image instructions]   │
└─────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

1. **Images as data URLs**: `data:image/png;base64,XXXX` format in the `images` array. Sidecar parses to extract media_type and raw base64.
2. **Images are per-request, not stored in session history**: Full image data is too large for conversation replay. Session stores a flag that images were attached.
3. **Existing IPC field**: `ChatRequest.images` was forward-planned in Phase 1 — no IPC schema changes needed.
4. **Supported formats**: JPEG, PNG, GIF, WebP (matches Anthropic API).

## Relevant Files

### To Modify
```
sidecar/caddee/services/claude_service.py  # Multimodal content blocks
sidecar/caddee/main.py                    # Pass images from request
sidecar/caddee/prompts/system_prompt.txt  # Image interpretation guidance
electron/src/renderer/hooks/useChat.ts    # Accept/send images
electron/src/renderer/components/ChatConsole.tsx  # Upload UI, preview, paste, drop
```

### Already Ready (no changes needed)
```
shared/messages.py   # ChatRequest.images already exists
shared/messages.ts   # ChatRequest.images already exists
electron/src/preload/index.ts  # sendToSidecar handles any SidecarRequest
```

## Step by Step Tasks

1. **Update claude_service.py for multimodal** — Accept `images: list[str] | None` in `call_claude()`. Parse data URLs to extract media_type and base64 data. Build Anthropic API multimodal content blocks (image + text) for the latest user message.

2. **Update main.py to pass images** — Extract `images` field from chat request dict. Pass to `call_claude()`. Don't store images in session (too large).

3. **Update system prompt for image interpretation** — Add instructions for interpreting sketches, photos, and technical drawings. Guide Claude on extracting dimensions, identifying shapes, and generating parametric .scad.

4. **Update useChat.ts to support images** — Modify `sendMessage()` to accept optional `images: string[]`. Include in the IPC `chat` request.

5. **Update ChatConsole.tsx with image upload UI** — Add paperclip button next to send. File picker for images (png/jpg/gif/webp). Image preview strip above textarea with remove buttons. Drag-and-drop on chat area. Clipboard paste (Cmd+V) for screenshots. Convert files to data URLs. Pass to sendMessage.

6. **Show images in chat message bubbles** — Update MessageBubble to render image thumbnails when a user message had images attached.

7. **Validation and backlog update** — Run all validation commands, check coding standards, update backlog status.

## Acceptance Criteria
- [ ] Paperclip button opens file picker for images
- [ ] Selected images show as thumbnails above the textarea
- [ ] Thumbnails have remove (X) buttons
- [ ] Drag-and-drop images onto chat area works
- [ ] Cmd+V paste from clipboard attaches screenshot
- [ ] Images are sent with the chat message to Claude
- [ ] Claude interprets images and generates .scad code
- [ ] User message bubbles show attached image thumbnails
- [ ] Multiple images can be attached to a single message
- [ ] Supported formats: JPEG, PNG, GIF, WebP
- [ ] Session save/restore works (images not stored, flag only)
