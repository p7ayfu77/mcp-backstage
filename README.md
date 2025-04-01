# Backstage MCP Server

An MCP (Model Context Protocol) server that connects to the Backstage API, exposing Backstage entities as resources and providing tools for read-only queries.

## Features

- **Backstage API Integration**: Connects to the Backstage Software Catalog API
- **Entity Resources**: Exposes Backstage entities as MCP resources
- **Query Tools**: Provides tools for read-only queries on Backstage entities
- **Analysis Prompts**: Includes prompts for common data analysis tasks

## Requirements

- Python 3.11+
- Backstage instance with API access

## Installation

Clone the repository and install the dependencies using UV:

```bash
uv pip install -e .
```

## Configuration

Set the following environment variables to configure the connection to Backstage:

- `BACKSTAGE_API_URL`: URL of your Backstage API (default: `http://localhost:7007/api`)
- `BACKSTAGE_TOKEN`: Authentication token for Backstage API (if required)

## Usage

### Running the Server

```bash
python -m main
```

### Available Resources

- `backstage://entities` - Get all entities from the Backstage catalog
- `backstage://entities/{kind}` - Get entities of a specific kind (e.g., component, api, system)
- `backstage://entity/{kind}/{namespace}/{name}` - Get a specific entity by its kind, namespace, and name

### Available Tools

- `query_entities` - Query entities using filter parameters
- `get_entity_relations` - Get relationships for a specific entity
- `search_entities` - Search entities by text
- `count_entities_by_kind` - Count entities by kind and return a summary

### Available Prompts

- `analyze_entities` - Analyze the entities in the Backstage catalog
- `analyze_component_dependencies` - Analyze dependencies for a specific component
- `system_health_check` - Check the health of the system based on Backstage data

## Example Usage with Claude or other MCP clients

1. Start the MCP server
2. Connect your MCP client (like Claude) to the server
3. Use resources like `backstage://entities` to retrieve data
4. Use tools like `query_entities` to filter and search

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.