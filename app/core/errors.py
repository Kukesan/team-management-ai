class ToolExecutionError(Exception):
    """Raised when a tool's underlying query fails or receives invalid input.
    Caught in the tool-calling loop and reported back to the model as a tool
    error rather than crashing the whole chat/summary request."""
