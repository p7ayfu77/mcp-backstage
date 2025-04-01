import os
import json
from typing import List, Dict, Any, Optional
import httpx
from mcp.server.fastmcp import FastMCP, Context, Image
from mcp.server.fastmcp.prompts import base

# Create a FastMCP server instance
mcp = FastMCP("Backstage MCP")

# Configuration for Backstage API
BACKSTAGE_API_URL = os.environ.get("BACKSTAGE_API_URL", "http://localhost:7007/api")
BACKSTAGE_TOKEN = os.environ.get("BACKSTAGE_TOKEN", "somethingrandom")

# Backstage API client
async def get_backstage_client():
    """Create an HTTP client for Backstage API with auth headers."""
    headers = {}
    if BACKSTAGE_TOKEN:
        headers["Authorization"] = f"Bearer {BACKSTAGE_TOKEN}"
    return httpx.AsyncClient(base_url=BACKSTAGE_API_URL, headers=headers)

# Resource to get all entities
@mcp.resource("backstage://entities")
async def get_all_entities() -> str:
    """Get all entities from the Backstage catalog."""
    async with await get_backstage_client() as client:
        response = await client.get("/catalog/entities")
        response.raise_for_status()
        entities = response.json()
        return json.dumps(entities, indent=2)

# Resource to get entities by kind
@mcp.resource("backstage://entities/{kind}")
async def get_entities_by_kind(kind: str) -> str:
    """Get entities of a specific kind from the Backstage catalog."""
    async with await get_backstage_client() as client:
        response = await client.get(f"/catalog/entities", params={"filter": f"kind={kind}"})
        response.raise_for_status()
        entities = response.json()
        return json.dumps(entities, indent=2)

# Resource to get a specific entity
@mcp.resource("backstage://entity/{kind}/{namespace}/{name}")
async def get_entity(kind: str, namespace: str, name: str) -> str:
    """Get a specific entity by its kind, namespace, and name."""
    async with await get_backstage_client() as client:
        response = await client.get(f"/catalog/entities/by-name/{kind}/{namespace}/{name}")
        response.raise_for_status()
        entity = response.json()
        return json.dumps(entity, indent=2)

# Tool to query entities with filter
@mcp.tool()
async def query_entities(filter_params: str) -> str:
    """
    Query entities from Backstage catalog using filter parameters.
    
    Example filter formats:
    - kind=component
    - kind=component,spec.type=service
    - metadata.annotations.backstage.io/orphan=true
    """
    async with await get_backstage_client() as client:
        params = {"filter": filter_params}
        response = await client.get("/catalog/entities", params=params)
        response.raise_for_status()
        entities = response.json()
        return json.dumps(entities, indent=2)

# Tool to get entity relationships
@mcp.tool()
async def get_entity_relations(kind: str, namespace: str, name: str) -> str:
    """Get all relationships for a specific entity."""
    async with await get_backstage_client() as client:
        response = await client.get(f"/catalog/entities/by-name/{kind}/{namespace}/{name}")
        response.raise_for_status()
        entity = response.json()
        
        if "relations" in entity:
            return json.dumps(entity["relations"], indent=2)
        else:
            return "No relationships found for this entity."

# Tool to search entities by text
@mcp.tool()
async def search_entities(query: str) -> str:
    """Search for entities using a text query."""
    async with await get_backstage_client() as client:
        response = await client.get("/catalog/entities/by-query", params={"fullTextFilter": query})
        response.raise_for_status()
        results = response.json()
        return json.dumps(results, indent=2)

# Tool to count entities by kind
@mcp.tool()
async def count_entities_by_kind() -> str:
    """Count entities by kind and return a summary."""
    async with await get_backstage_client() as client:
        response = await client.get("/catalog/entities")
        response.raise_for_status()
        entities_response = response.json()
        
        # Debug the structure of the response
        response_structure = f"Response keys: {list(entities_response.keys()) if isinstance(entities_response, dict) else 'Not a dict'}"
        
        kind_counts = {}
        
        # Handle both possible response structures
        if isinstance(entities_response, dict) and 'items' in entities_response:
            # Backstage returns entities in an 'items' array
            items = entities_response['items']
        elif isinstance(entities_response, list):
            # The response might be a direct list of entities
            items = entities_response
        else:
            return f"Unexpected response structure: {response_structure}"
        
        # Count entities by kind
        for entity in items:
            # Ensure case-insensitive matching for kind
            kind = entity.get('kind')
            if kind:
                # Convert to title case for consistent display
                kind_title = kind.title()
                if kind_title in kind_counts:
                    kind_counts[kind_title] += 1
                else:
                    kind_counts[kind_title] = 1
        
        result = {
            "counts": kind_counts,
            "total": sum(kind_counts.values()),
            "debug_info": response_structure
        }
        
        return json.dumps(result, indent=2)

# New tool to find entities by annotation
@mcp.tool()
async def find_entities_by_annotation(annotation_key: str, annotation_value: Optional[str] = None) -> str:
    """
    Find entities that have a specific annotation key or key-value pair.
    
    Args:
        annotation_key: The annotation key to search for (e.g., 'example.com/service-discovery')
        annotation_value: Optional value to match with the annotation key
        
    Returns:
        JSON string containing matching entities
    """
    async with await get_backstage_client() as client:
        # Get all entities first since Backstage API doesn't directly support annotation filtering
        response = await client.get("/catalog/entities")
        response.raise_for_status()
        
        entities_response = response.json()
        matching_entities = []
        
        # Process as either list or dict with 'items'
        items = []
        if isinstance(entities_response, dict) and 'items' in entities_response:
            items = entities_response['items']
        elif isinstance(entities_response, list):
            items = entities_response
            
        # Filter entities by annotation
        for entity in items:
            annotations = entity.get('metadata', {}).get('annotations', {})
            
            # Check if the annotation key exists
            if annotation_key in annotations:
                # If annotation_value is specified, check if it matches
                if annotation_value is None or annotations[annotation_key] == annotation_value:
                    matching_entities.append(entity)
        
        result = {
            "total": len(matching_entities),
            "items": matching_entities
        }
        
        return json.dumps(result, indent=2)

# Tool to get all annotation keys
@mcp.tool()
async def list_annotation_keys() -> str:
    """
    List all unique annotation keys used across entities in the Backstage catalog.
    
    Returns:
        JSON string with lists of annotation keys and their usage counts
    """
    async with await get_backstage_client() as client:
        response = await client.get("/catalog/entities")
        response.raise_for_status()
        
        entities_response = response.json()
        annotation_counts = {}
        
        # Process as either list or dict with 'items'
        items = []
        if isinstance(entities_response, dict) and 'items' in entities_response:
            items = entities_response['items']
        elif isinstance(entities_response, list):
            items = entities_response
            
        # Count annotations
        for entity in items:
            annotations = entity.get('metadata', {}).get('annotations', {})
            for key in annotations:
                if key in annotation_counts:
                    annotation_counts[key] += 1
                else:
                    annotation_counts[key] = 1
        
        # Sort by frequency
        sorted_annotations = sorted(annotation_counts.items(), key=lambda x: x[1], reverse=True)
        
        result = {
            "total_unique_keys": len(sorted_annotations),
            "keys": [{"key": key, "count": count} for key, count in sorted_annotations]
        }
        
        return json.dumps(result, indent=2)

# Prompt for entity analysis
@mcp.prompt()
def analyze_entities() -> str:
    """Analyze the entities in the Backstage catalog."""
    return """
    I need to analyze the entities in our Backstage catalog.
    
    First, please get all entities using the backstage://entities resource.
    Then, help me understand:
    1. How many entities of each kind do we have?
    2. What are the main component types?
    3. How are our services interconnected?
    4. Are there any orphaned entities?
    
    Please provide visualizations or summaries where appropriate.
    """

# Prompt for component dependencies
@mcp.prompt()
def analyze_component_dependencies(component_name: str) -> str:
    """Analyze dependencies for a specific component."""
    return f"""
    I need to analyze the dependencies for the component named '{component_name}'.
    
    Please:
    1. Get the component entity details
    2. Identify all its dependencies and dependents
    3. Create a dependency graph or visualization if possible
    4. Highlight any critical paths or potential issues
    
    This will help me understand the impact of changes to this component.
    """

# Prompt for system health check
@mcp.prompt()
def system_health_check() -> list[base.Message]:
    """Check the health of the system based on Backstage data."""
    return [
        base.UserMessage("""
        I need a health check of our system based on Backstage data.
        
        Please analyze:
        1. Service health indicators
        2. API status
        3. Recent deployments
        4. Any critical issues or warnings
        
        This will give me a quick overview of the current system status.
        """),
        
        base.AssistantMessage("""
        I'll perform a system health check based on Backstage data.
        
        First, let me gather information about your services...
        """)
    ]

# New prompt for service discovery
@mcp.prompt()
def discover_service(service_id: str) -> str:
    """Find and analyze a service by its service discovery ID."""
    return f"""
    I need to find the service with service discovery ID '{service_id}' in our Backstage catalog.
    
    Please:
    1. Search for entities with the annotation 'example.com/service-discovery' matching this ID
    2. Get detailed information about the found component
    3. Identify its dependencies, consumers, and the system it belongs to
    4. Show any APIs it provides or consumes
    5. Determine its current deployment environment from labels
    
    This will help me understand this service's role and connections in our architecture.
    """

# New prompt for annotation analysis
@mcp.prompt()
def analyze_annotations() -> str:
    """Analyze annotations used across entities in the catalog."""
    return """
    I need to analyze the annotations used in our Backstage catalog.
    
    Please:
    1. Get a list of all annotation keys and their usage counts
    2. Identify any custom annotations vs standard Backstage annotations
    3. Show examples of entities using custom annotations
    4. Suggest how these annotations could be leveraged for better integration
    
    This will help me understand how we're extending Backstage with custom metadata.
    """

def main():
    """Run the Backstage MCP server."""
    print(f"Starting Backstage MCP server...")
    print(f"Connecting to Backstage API at: {BACKSTAGE_API_URL}")
    mcp.run()

if __name__ == "__main__":
    main()
