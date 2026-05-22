# Second Brain Obsidian Plugin

Integrates Obsidian with the Second Brain knowledge system for semantic search, entity exploration, and graph visualization.

## Features

- **Semantic Search**: Search your knowledge base using natural language queries
- **Entity Browser**: Browse and explore entities in your knowledge graph
- **Relationship Viewer**: See relationships between entities
- **Graph Explorer**: Navigate through the knowledge graph with adjustable depth

## Installation

1. Extract the plugin to your Obsidian plugins folder:
   ```
   .obsidian/plugins/second-brain-plugin/
   ```

2. Enable the plugin in Obsidian settings

3. Configure the API URL in the plugin settings (default: http://localhost:8000)

## Usage

### Commands

Access commands via Cmd+P (Mac) or Ctrl+P (Windows/Linux):

- **Search Second Brain**: Open search modal to query your knowledge base
- **Entity Detail**: View detailed information about an entity
- **Graph Explorer**: Explore the knowledge graph

### Configuration

1. Open Obsidian Settings
2. Go to "Second Brain Plugin" settings
3. Enter your API URL (e.g., http://localhost:8000)

## Development

### Setup

```bash
npm install
```

### Build for Development

```bash
npm run dev
```

### Build for Production

```bash
npm run build
```

## Architecture

- `SecondBrainPlugin.ts`: Main plugin class handling initialization and commands
- `SettingsTab.ts`: Settings UI for configuring the plugin
- `SearchModal.ts`: Search interface for querying the API

## API Integration

The plugin connects to a Second Brain backend API at the configured URL. It supports:

- POST `/search` - Semantic search
- GET `/graph/entity/{id}` - Entity details
- POST `/graph/traverse` - Graph traversal

## License

MIT
