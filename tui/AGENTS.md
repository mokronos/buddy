# buddy tui guidelines

## Build/Test Commands

- **Install**: `bun install`
- **Run**: `bun run dev`
- **Typecheck**: `bun run typecheck` (npm run typecheck)
- **Test**: `bun test` (runs all tests)
- **Single test**: `bun test test/tool/tool.test.ts` (specific test file)

## Code Style

- **Runtime**: Bun with TypeScript ESM modules
- **Imports**: Use relative imports for local modules, named imports preferred
- **Types**: Zod schemas for validation, TypeScript interfaces for structure
- **Naming**: camelCase for variables/functions, PascalCase for classes/namespaces
- **Error handling**: Use Result patterns
- **File structure**: Namespace-based organization (e.g., `Tool.define()`, `Session.create()`)


## OpenTUI

- check ../opentui for the opentui library code and docs
