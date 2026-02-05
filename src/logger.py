"""Simple logging system for conversation history and tool usage"""

import json
import os
from datetime import datetime
from pathlib import Path


class ConversationLogger:
    """Logs conversations and tool calls to JSON files"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create a new session file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_file = self.log_dir / f"session_{timestamp}.json"
        
        self.session_data = {
            "session_start": datetime.now().isoformat(),
            "conversations": []
        }
        self._save()
    
    def _save(self):
        """Save session data to file"""
        with open(self.session_file, "w") as f:
            json.dump(self.session_data, f, indent=2, default=str)
    
    def log_user_message(self, message: str):
        """Log a user message"""
        self.session_data["conversations"].append({
            "timestamp": datetime.now().isoformat(),
            "type": "user_message",
            "content": message
        })
        self._save()
    
    def log_tool_call(self, tool_name: str, parameters: dict, result: any):
        """Log a tool call with its parameters and result"""
        self.session_data["conversations"].append({
            "timestamp": datetime.now().isoformat(),
            "type": "tool_call",
            "tool_name": tool_name,
            "parameters": parameters,
            "result_preview": self._truncate_result(result)
        })
        self._save()
    
    def log_assistant_response(self, response: any):
        """Log assistant response"""
        # Handle both string and FeasibilityResponse objects
        if hasattr(response, "model_dump"):
            content = response.model_dump()
        elif hasattr(response, "__dict__"):
            content = response.__dict__
        else:
            content = str(response)
        
        self.session_data["conversations"].append({
            "timestamp": datetime.now().isoformat(),
            "type": "assistant_response",
            "content": content
        })
        self._save()
    
    def log_error(self, error: Exception):
        """Log an error"""
        self.session_data["conversations"].append({
            "timestamp": datetime.now().isoformat(),
            "type": "error",
            "error_type": type(error).__name__,
            "error_message": str(error)
        })
        self._save()
    
    def log_memory_cleared(self):
        """Log when memory is cleared"""
        self.session_data["conversations"].append({
            "timestamp": datetime.now().isoformat(),
            "type": "memory_cleared"
        })
        self._save()
    
    def _truncate_result(self, result: any, max_length: int = 1000) -> any:
        """Truncate large results for logging"""
        if isinstance(result, str):
            if len(result) > max_length:
                return result[:max_length] + "... [truncated]"
            return result
        elif isinstance(result, dict):
            result_str = json.dumps(result, default=str)
            if len(result_str) > max_length:
                return {"_preview": result_str[:max_length] + "... [truncated]"}
            return result
        elif isinstance(result, list):
            result_str = json.dumps(result, default=str)
            if len(result_str) > max_length:
                return {"_preview": f"List with {len(result)} items", "_sample": result[:2] if result else []}
            return result
        return str(result)[:max_length]
    
    def get_session_file(self) -> str:
        """Return the current session file path"""
        return str(self.session_file)


# Optional: Pretty print for console logging
def print_tool_call(tool_name: str, parameters: dict):
    """Pretty print a tool call to console"""
    print(f"\n{'='*50}")
    print(f"🔧 TOOL CALL: {tool_name}")
    print(f"{'='*50}")
    print("📥 Parameters:")
    for key, value in parameters.items():
        print(f"   • {key}: {value}")
    print()

