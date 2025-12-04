from fastmcp import FastMCP
import random

mcp = FastMCP("Utility Tools Server")


# -------------------------
# TOOL 1: ADD TWO NUMBERS
# -------------------------
@mcp.tool()
def add_numbers(a: float, b: float):
    """Add two numbers and return the sum."""
    return {"result": a + b}


# -------------------------
# TOOL 2: RANDOM NUMBER
# -------------------------
@mcp.tool()
def random_number(min_value: int = 1, max_value: int = 100):
    """Generate a random number between min_value and max_value."""
    return {"random": random.randint(min_value, max_value)}


# -------------------------
# RESOURCE: SIMPLE INFO
# -------------------------
# Must be a valid URL-like format
@mcp.resource("resource://basic_info")
def basic_info():
    """Basic server information without psutil/platform/socket."""
    return {
        "status": "running",
        "message": "FastMCP server is active",
        "tips": "Add psutil/system info later if needed",
    }


# -------------------------
# START SERVER (HTTP)
# -------------------------
if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000
    )
