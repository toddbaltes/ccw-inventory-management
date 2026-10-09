# CLAUDE.md

Factory Inventory Management System Demo with GitHub integration - Full-stack application with Vue 3 frontend, Python FastAPI backend, and in-memory mock data (no database).

## Critical Tool Usage Rules

### Subagents
Use the Task tool with these specialized subagents for appropriate tasks:

- **vue-expert**: Use for Vue 3 frontend features, UI components, styling, and client-side functionality
  - Examples: Creating components, fixing reactivity issues, performance optimization, complex state management
  - **MANDATORY RULE: ANY time you need to create or significantly modify a .vue file, you MUST delegate to vue-expert**
- **code-reviewer**: Use after writing significant code to review quality and best practices
- **Explore**: Use for understanding codebase structure, searching for patterns, or answering questions about how components work
- **general-purpose**: Use for complex multi-step tasks or when other agents don't fit

### Skills
- **backend-api-test** skill: Use when writing or modifying tests in `tests/backend` directory with pytest and FastAPI TestClient

### MCP Tools
- **ALWAYS use GitHub MCP tools** (`mcp__github__*`) for ALL GitHub operations
  - Exception: Local branches only - use `git checkout -b` instead of `mcp__github__create_branch`
- **ALWAYS use Playwright MCP tools** (`mcp__playwright__*`) for browser testing
  - Test against: `http://localhost:3000` (frontend), `http://localhost:8001` (API)

## Stack
- **Frontend**: Vue 3 + Composition API + Vite (port 3000)
- **Backend**: Python FastAPI (port 8001)
- **Data**: JSON files in `server/data/` loaded via `server/mock_data.py`

## Quick Start

```bash
# Backend
cd server
uv run python main.py

# Frontend
cd client
npm install && npm run dev
```

## Key Patterns

**Filter System**: 4 filters (Time Period, Warehouse, Category, Order Status) apply to all data via query params
**Data Flow**: Vue filters → `client/src/api.js` → FastAPI → In-memory filtering → Pydantic validation → Computed properties
**Reactivity**: Raw data in refs (`allOrders`, `inventoryItems`), derived data in computed properties

## API Endpoints
- `GET /api/inventory` - Filters: warehouse, category
- `GET /api/orders` - Filters: warehouse, category, status, month
- `GET /api/dashboard/summary` - All filters
- `GET /api/demand`, `/api/backlog` - No filters
- `GET /api/spending/*` - Summary, monthly, categories, transactions

## Common Issues
1. Use unique keys in v-for (not `index`) - use `sku`, `month`, etc.
2. Validate dates before `.getMonth()` calls
3. Update Pydantic models when changing JSON data structure
4. Inventory filters don't support month (no time dimension)
5. Revenue goals: $800K/month single, $9.6M YTD all months

## File Locations
- Views: `client/src/views/*.vue`
- API Client: `client/src/api.js`
- Backend: `server/main.py`, `server/mock_data.py`
- Data: `server/data/*.json`
- Styles: `client/src/styles/tokens.css` (design tokens), `client/src/styles/base.css` (shared classes), `client/src/App.vue` (sidebar/top bar shell)

## Design System
- Custom CSS only (Tailwind is not installed). All colors, type, radius, shadow and spacing come from CSS variables in `client/src/styles/tokens.css`; use `var(--...)`, never hardcoded hex or `!important`
- Layout: fixed left sidebar + sticky top bar (filters, language, profile); sidebar becomes a slide-over at 1024px and below
- Neutrals: slate (`--slate-50` to `--slate-900`); text `--color-text`, `--color-text-muted`; borders `--color-border`
- Brand accent: red `--brand` (#E4002B), only for primary buttons, active nav, focus rings and links
- Status: `--success` green, `--info` blue, `--warning` amber, `--danger` crimson (#b42318, deliberately distinct from brand red), each with `-dark` (use for small text) and `-tint` (backgrounds) variants
- Font: Inter (`--font-sans`)
- Shared classes in `base.css`: `.card`, `.stat-card`, `.btn` (`-primary`, `-secondary`, `-ghost`, `-sm`), `.badge`, tables, form controls, `.modal-*`, `.info-grid`, `.row-clickable`; reuse these instead of redefining them in scoped styles
- Charts: Custom SVG / CSS bars with flat `--chart-*` token colors, CSS Grid for layouts
- No emojis in UI
