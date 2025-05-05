# server.py
import httpx
import json
import os
from typing import Optional, List, Dict, Any, Literal
from fastmcp import FastMCP

# Create MCP Server Instance
mcp = FastMCP("ScopeGreen LCA", dependencies=["httpx"])

@mcp.tool()
async def search_lca_metrics(
    item_name: str,
    metric: Optional[Literal["Carbon footprint", "EF3.1 Score", "Land Use"]] = "Carbon footprint",
    year: Optional[str] = None,
    geography: Optional[str] = None,
    num_matches: Optional[Literal[1, 2, 3]] = 1,
    unit: Optional[str] = None,
    mode: Optional[Literal["lite", "pro"]] = "lite",
    domain: Optional[Literal["Materials & Products", "Processing", "Transport", "Energy", "Direct emissions"]] = None,
    not_english: Optional[bool] = False
) -> Dict[str, Any]:
    """
    Searches the ScopeGreen API for Life Cycle Assessment (LCA) metrics for specific items, processes, or energy types.
    Provides environmental impact data like carbon footprint.

    IMPORTANT: Use the 'domain' parameter to get accurate results, especially for ambiguous items like 'electricity'.
    If an exact geographical match isn't found, data for a broader region (e.g., 'EU' instead of 'DE') might be returned as the best proxy.
    The 'explanation' field in the results describes the match quality and any proxies used.

    Args:
        item_name: Name of the item, material, process, or energy type (e.g., 'cotton t-shirt', 'steel beam', 'electricity grid mix'). Be specific for best results. REQUIRED.
        metric: The specific environmental metric (e.g., 'Carbon footprint', 'EF3.1 Score', 'Land Use'). Defaults to 'Carbon footprint'.
        year: Year of the requested data (e.g., '2022', '2025'). Format YYYY. Must be >= 2020 if specified.
        geography: Region for the requested data. Use ISO 3166-1 alpha-2 codes (e.g., 'DE', 'US', 'FR') or broader regions ('EU', 'Global'). If omitted or unavailable, may return data for a parent region.
        num_matches: How many ranked matches to return (1, 2, or 3). Defaults to 1.
        unit: Request conversion to a specific functional unit (e.g., 'g', 'kg/m2', 'kg CO2 eq / kWh'). If conversion is not possible or requested, original units are returned. Check API docs for details.
        mode: Performance mode ('lite' or 'pro'). Currently 'pro' executes as 'lite'. Defaults to 'lite'.
        domain: VERY IMPORTANT filter for context. Use 'Energy' for electricity generation/consumption, 'Transport' for transportation methods, 'Processing' for industrial processes, 'Materials & Products' for goods. If omitted (None), defaults to 'Materials & Products' on the backend, which may yield incorrect results for non-product items.
        not_english: Set to true if the item_name is not in English to enable auto-translation. Defaults to false.

    Returns:
        A dictionary containing the search results ('matches' and 'explanation')
        or a message indicating no match was found.
    """
    # Get the API key from the environment variable (set by Claude Desktop config)
    api_key = os.getenv("SCOPEGREEN_API_KEY")
    if not api_key:
        return {"error": "SCOPEGREEN_API_KEY not found in environment variables"}

    # Base URL from docs
    BASE_URL = "https://scopegreen-main-1a948ab.d2.zuplo.dev"
    
    # --- Set default domain if not provided by LLM ---
    effective_domain = domain if domain is not None else "Materials & Products"
    print(f"Executing ScopeGreen search for: '{item_name}' in domain '{effective_domain}'")

    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "item_name": item_name,
        "metric": metric,
        "year": year,
        "geography": geography,
        "num_matches": num_matches,
        "unit": unit,
        "mode": mode,
        "domain": effective_domain,
        "not_english": not_english,
    }
    # Filter out parameters with None values (except domain, which we defaulted)
    filtered_params = {k: v for k, v in params.items() if v is not None}

    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers) as client:
        try:
            print(f"Calling API with params: {filtered_params}")
            response = await client.get("/api/metrics/search", params=filtered_params)
            response.raise_for_status()
            print(f"API Response Status: {response.status_code}")
            return response.json()
        except httpx.HTTPStatusError as exc:
            print(f"HTTP error occurred: {exc.response.status_code} - {exc.response.text}")
            try:
                error_detail = exc.response.json()
            except json.JSONDecodeError:
                error_detail = exc.response.text
            return {"error": f"API request failed with status {exc.response.status_code}", "details": error_detail}
        except httpx.RequestError as exc:
            print(f"Request error occurred: {exc}")
            return {"error": "Failed to connect to the ScopeGreen API."}
        except Exception as exc:
            print(f"An unexpected error occurred: {exc}")
            return {"error": "An unexpected error occurred during the API call."}

@mcp.tool()
async def get_available_metrics() -> Dict[str, List[str]]:
    """Gets the list of available metric types from the ScopeGreen API."""
    api_key = os.getenv("SCOPEGREEN_API_KEY")
    if not api_key:
        return {"error": "SCOPEGREEN_API_KEY not found in environment variables"}
        
    BASE_URL = "https://scopegreen-main-1a948ab.d2.zuplo.dev"
    print("Executing ScopeGreen get_available_metrics")
    
    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers) as client:
        try:
            response = await client.get("/api/metrics/available")
            response.raise_for_status()
            print(f"API Response Status: {response.status_code}")
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
    print(f"Starting ScopeGreen LCA MCP Server, using base URL: https://scopegreen-main-1a948ab.d2.zuplo.dev")
    print("Ensure Claude Desktop config contains SCOPEGREEN_API_KEY")
    mcp.run()