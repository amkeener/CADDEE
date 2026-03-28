# TypeScript / React Coding Standards

Applies to: `electron/src/**/*.ts`, `electron/src/**/*.tsx`, `shared/*.ts`

## Language & Tooling

- **TypeScript** with `strict: true` — no `any` unless unavoidable (add inline `// eslint-disable` comment with reason)
- **Target:** ES2022, module ESNext, bundler resolution
- **Build:** electron-vite (Vite-based)
- **Type-check:** `cd electron && npx tsc --noEmit` — must pass with zero errors

## React Conventions

- **Functional components only** — no class components
- **Hooks for state** — `useState`, `useRef`, `useCallback`, `useEffect`
- **No external state libraries** (no Redux, Zustand, Jotai, etc.) — state lives in `App.tsx` and flows down via props
- **No external component libraries** (no MUI, Chakra, etc.) — components are self-contained
- **`useCallback`** for all handler functions passed as props to child components
- **`crypto.randomUUID()`** for generating request IDs

## Styling

- **Inline CSS-in-JS only** — `const styles: Record<string, React.CSSProperties> = { ... }`
- **No CSS files, no Tailwind, no styled-components, no CSS modules**
- **Dark theme palette:**
  - Backgrounds: `#0f0f23`, `#1a1a2e`
  - Text: `#ccc` (body), `#fff` (headings/emphasis)
  - Borders: `#2a2a3e`, `#333`
  - Accent: `#7c8aff`

## IPC & Preload

- All sidecar communication goes through `window.caddee.sendToSidecar()` — never call Electron IPC directly from renderer
- New IPC methods require changes in **three files**: `preload/index.ts`, `main/ipc-handlers.ts`, and the `CaddeeAPI` type
- Message types are defined in `shared/messages.ts` — keep in sync with `shared/messages.py`

## Three.js

- Viewport.tsx owns the Three.js scene — don't create secondary scenes
- Dispose geometries, materials, and textures on component unmount
- STL loading: use `STLLoader` from `three/examples/jsm/loaders/STLLoader`
- Base64 STL → ArrayBuffer: `atob()` + `Uint8Array` pattern

## Naming

- **Files:** PascalCase for components (`ChatConsole.tsx`), camelCase for utilities (`scadParser.ts`)
- **Components:** PascalCase (`export function ChatConsole()`)
- **Hooks:** camelCase with `use` prefix (`useChat.ts`)
- **Interfaces/types:** PascalCase (`ChatMessage`, `SidecarRequest`)
- **Props interfaces:** `{ComponentName}Props` when extracted, or inline
- **Constants:** camelCase for local, UPPER_SNAKE for module-level true constants

## Imports

- React imports first, then third-party, then local — separated by blank lines
- Use relative imports within `electron/src/`
- Use `type` keyword for type-only imports: `import type { Foo } from './types'`

## Error Handling

- Async IPC calls: wrap in try/catch, surface errors to user via chat or toast
- Three.js resource cleanup: always in `useEffect` cleanup functions
- Don't swallow errors silently — at minimum log to console

## Validation (enforced during build/review)

```bash
cd electron && npx tsc --noEmit
```
