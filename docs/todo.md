# Open TODOs

## Proxy/card behavior

- Keep evaluating whether card URL rewriting can be removed.
- Current behavior rewrites card `url` so JS A2A clients keep routing through Buddy proxy paths.
- Cleaner long-term target:
  1. Registry is authoritative transport route (`/a2a/{kind}/{id}`).
  2. Frontend pins transport to registry route.
  3. Agent cards are metadata, not routing authority.
  4. Proxy can pass card payloads through unchanged (or only rewrite in compatibility mode).

## Documentation hygiene

- Keep docs aligned with package-based layout under `packages/`.
- Update docs whenever route/module moves occur (for example route files under `control_plane/routes/`).
