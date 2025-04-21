# server.py
import httpx
import json
import os
from dotenv import load_dotenv
from fastmcp import FastMCP
import pathlib
from typing import Optional, List, Dict, Any, Literal # Added Literal

# --- Get the directory where this script is located ---
SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()

# --- Configuration ---
BASE_URL = "https://lcabench-v1-main-3f150df.d2.zuplo.dev" # Base URL from docs

# Load environment variables from .env file (should be in SCRIPT_DIR)
load_dotenv(dotenv_path=SCRIPT_DIR / ".env")

# Get the API key from the environment variable
api_key = os.getenv("SCOPEGREEN_API_KEY")
if not api_key:
    raise ValueError("SCOPEGREEN_API_KEY not found in environment variables or .env file")

# --- Create MCP Server Instance ---
# Add dependencies needed for installation
mcp = FastMCP("ScopeGreen LCA", dependencies=["httpx", "python-dotenv"])

# --- Define Tools ---

@mcp.tool()
async def search_lca_metrics(
    item_name: str,
    metric: Optional[Literal["Carbon footprint", "EF3.1 Score", "Land Use"]] = "Carbon footprint",
    year: Optional[str] = None,
    geography: Optional[str] = None,
    num_matches: Optional[Literal[1, 2, 3]] = 1,
    unit: Optional[str] = None,
    mode: Optional[Literal["lite", "pro"]] = "lite",
    domain: Optional[Literal["Materials & Products", "Processing", "Transport", "Energy", "Direct emissions"]] = "Materials & Products",
    not_english: Optional[bool] = False
) -> Dict[str, Any]:
    """
    Searches the ScopeGreen API for Life Cycle Assessment (LCA) metrics.

    Args:
        item_name: Name of the item or material to find metrics for (e.g., 'cotton t-shirt', 'steel beam'). REQUIRED.
        metric: The specific metric to retrieve (e.g., 'Carbon footprint', 'EF3.1 Score', 'Land Use'). Defaults to 'Carbon footprint'.
        year: Year of the requested data (e.g., '2022'). Must be >= 2020 if specified.
        geography: Region for the requested data (e.g., 'FR', 'EU', 'Global').
        num_matches: How many ranked matches to return (1, 2, or 3). Defaults to 1.
        unit: Request conversion to a specific functional unit (e.g., 'g', 'kg/m2'). See API docs for details.
        mode: Performance mode ('lite' or 'pro'). Currently 'pro' executes as 'lite'. Defaults to 'lite'.
        domain: Filter by domain ('Materials & Products', 'Processing', 'Transport', 'Energy', 'Direct emissions'). Defaults to 'Materials & Products'.
        not_english: Set to true if the item_name is not in English to enable auto-translation. Defaults to false.

    Returns:
        A dictionary containing the search results ('matches' and 'explanation')
        or a message indicating no match was found.
    """
    print(f"Executing ScopeGreen search for: {item_name}") # Add print statement for debugging
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "item_name": item_name,
        "metric": metric,
        "year": year,
        "geography": geography,
        "num_matches": num_matches,
        "unit": unit,
        "mode": mode,
        "domain": domain,
        "not_english": not_english,
        # Add other parameters from OAS if needed, filtering None values
    }
    # Filter out parameters with None values
    filtered_params = {k: v for k, v in params.items() if v is not None}

    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers) as client:
        try:
            response = await client.get("/api/metrics/search", params=filtered_params)
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            print(f"API Response Status: {response.status_code}") # Debugging
            # print(f"API Response Content: {response.text}") # More Debugging (optional)
            return response.json()
        except httpx.HTTPStatusError as exc:
            print(f"HTTP error occurred: {exc.response.status_code} - {exc.response.text}")
            return {"error": f"API request failed with status {exc.response.status_code}", "details": exc.response.text}
        except httpx.RequestError as exc:
            print(f"Request error occurred: {exc}")
            return {"error": "Failed to connect to the ScopeGreen API."}
        except Exception as exc:
            print(f"An unexpected error occurred: {exc}")
            return {"error": "An unexpected error occurred during the API call."}

@mcp.tool()
async def get_available_metrics() -> Dict[str, List[str]]:
    """Gets the list of available metric types from the ScopeGreen API."""
    print("Executing ScopeGreen get_available_metrics") # Debugging
    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers) as client:
        try:
            response = await client.get("/api/metrics/available")
            response.raise_for_status()
            print(f"API Response Status: {response.status_code}") # Debugging
            return response.json()
        except httpx.HTTPStatusError as exc:
            print(f"HTTP error occurred: {exc.response.status_code} - {exc.response.text}")
            return {"error": f"API request failed with status {exc.response.status_code}", "details": exc.response.text}
        except httpx.RequestError as exc:
            print(f"Request error occurred: {exc}")
            return {"error": "Failed to connect to the ScopeGreen API."}
        except Exception as exc:
            print(f"An unexpected error occurred: {exc}")
            return {"error": "An unexpected error occurred during the API call."}

# --- Run the Server ---
if __name__ == "__main__":
    print(f"Starting ScopeGreen LCA MCP Server (Manual Tools), using base URL: {BASE_URL}")
    print("Ensure your .env file contains SCOPEGREEN_API_KEY")
    mcp.run() # Use 'mcp' instance here