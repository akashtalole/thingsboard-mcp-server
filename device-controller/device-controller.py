from typing import Any, Optional
import httpx
from mcp.server.fastmcp import FastMCP
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("thingsboard")

# Environment variables
THINGSBOARD_API_BASE = os.getenv("THINGSBOARD_API_BASE", None)
THINGSBOARD_USERNAME = os.getenv("THINGSBOARD_USERNAME", None)
THINGSBOARD_PASSWORD = os.getenv("THINGSBOARD_PASSWORD", None)

# Global variable to store the auth token
auth_token: Optional[str] = None

# Constants
USER_AGENT = "thingsboard-app/1.0"

def get_auth_token(username: str, password: str) -> str:
    """Get the auth token from Thingsboard API."""
    try:
        url = f"{THINGSBOARD_API_BASE}/api/auth/login"
        headers = {
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json"
        }
        payload = {
            "username": username,
            "password": password
        }
        response = httpx.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get("token")
        else:
            return None
    except Exception as e:
        raise Exception(f"Error getting auth token: {e}")

async def make_tb_request(url: str, params: Optional[dict] = None) -> dict[str, Any] | None:
    """Make a request to the Thingsboard API with proper error handling."""
    global auth_token

    if not auth_token:
        auth_token = get_auth_token(THINGSBOARD_USERNAME, THINGSBOARD_PASSWORD)
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

@mcp.tool()
async def getDevicesByIds(deviceIds : str) -> str:
    """Get device by device ID.

    Args:
        deviceIds : A list of devices ids, separated by comma ','
    """
    url = f"{THINGSBOARD_API_BASE}/api/devices?{deviceIds}"
    params = {
        "deviceIds": deviceIds
    }
    return await make_tb_request(url, params)

@mcp.tool()
async def getDeviceInfoById(deviceId : str) -> str:
    """Get device info.

    Args:
        deviceId : The device id to get info for.
    """
    # First get the forecast grid endpoint
    url = f"{THINGSBOARD_API_BASE}/api/device/info/{deviceId}"
    params = {
        "deviceId": deviceId
    }
    return await make_tb_request(url, params) 

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='sse')