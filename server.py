from app import mcp  # noqa: F401 - imports auth/mcp setup

# Register tools from each module
import services  # noqa: E402, F401
import registrations  # noqa: E402, F401
import giving  # noqa: E402, F401
import calendar_events  # noqa: E402, F401
import people  # noqa: E402, F401
import groups  # noqa: E402, F401

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
