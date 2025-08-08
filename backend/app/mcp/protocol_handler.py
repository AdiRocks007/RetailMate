"""
MCP Protocol Handler for RetailMate
Handles JSON-RPC 2.0 message processing and validation
Based on official MCP specification v1.0
"""

import json
import logging
from typing import Any, Dict, Optional, Union, List
from pydantic import BaseModel, Field, ValidationError
from enum import Enum

logger = logging.getLogger("retailmate-mcp-protocol")

class MCPErrorCode(Enum):
    """Standard JSON-RPC 2.0 error codes"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

class MCPMessage(BaseModel):
    """Base MCP message model"""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    id: Optional[Union[str, int]] = Field(default=None, description="Message ID")

class MCPRequest(MCPMessage):
    """MCP request message"""
    method: str = Field(description="Method name")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Method parameters")

class MCPResponse(MCPMessage):
    """MCP response message"""
    result: Optional[Any] = Field(default=None, description="Method result")
    error: Optional[Dict[str, Any]] = Field(default=None, description="Error information")

class MCPError(BaseModel):
    """MCP error structure"""
    code: int = Field(description="Error code")
    message: str = Field(description="Error message")
    data: Optional[Any] = Field(default=None, description="Additional error data")

class MCPProtocolHandler:
    """Handles MCP protocol message processing"""
    
    def __init__(self):
        # Based on MCP specification v1.0
        self.supported_methods = {
            "initialize",
            "initialized",
            "tools/list",
            "tools/call",
            "resources/list",
            "resources/read",
            "resources/subscribe",
            "resources/unsubscribe",
            "prompts/list",
            "prompts/get",
            "completion/complete",
            "logging/setLevel",
            "ping"
        }
        
        self.message_history: List[MCPMessage] = []
        self.error_count = 0
        
        logger.info("MCP Protocol Handler initialized (MCP v1.0 compatible)")
    
    def validate_request(self, raw_message: str) -> Union[MCPRequest, MCPError]:
        """Validate incoming MCP request against specification"""
        try:
            # Parse JSON
            if not raw_message.strip():
                return MCPError(
                    code=MCPErrorCode.PARSE_ERROR.value,
                    message="Empty message received",
                    data={"raw_message": raw_message}
                )
            
            message_data = json.loads(raw_message)
            
            # Validate JSON-RPC version
            if message_data.get("jsonrpc") != "2.0":
                return MCPError(
                    code=MCPErrorCode.INVALID_REQUEST.value,
                    message="Invalid JSON-RPC version. Must be '2.0'",
                    data={"received_version": message_data.get("jsonrpc")}
                )
            
            # Validate against MCP request schema
            request = MCPRequest(**message_data)
            
            # Check if method is supported
            if request.method not in self.supported_methods:
                return MCPError(
                    code=MCPErrorCode.METHOD_NOT_FOUND.value,
                    message=f"Method not found: {request.method}",
                    data={
                        "supported_methods": sorted(list(self.supported_methods)),
                        "requested_method": request.method
                    }
                )
            
            # Store valid request in history
            self.message_history.append(request)
            if len(self.message_history) > 100:  # Keep last 100 messages
                self.message_history.pop(0)
            
            return request
            
        except json.JSONDecodeError as e:
            self.error_count += 1
            return MCPError(
                code=MCPErrorCode.PARSE_ERROR.value,
                message="Parse error: Invalid JSON",
                data={
                    "details": str(e),
                    "position": getattr(e, 'pos', None),
                    "raw_message_preview": raw_message[:100] + "..." if len(raw_message) > 100 else raw_message
                }
            )
        except ValidationError as e:
            self.error_count += 1
            return MCPError(
                code=MCPErrorCode.INVALID_REQUEST.value,
                message="Invalid request format",
                data={
                    "validation_errors": [
                        {
                            "field": error["loc"][-1] if error["loc"] else "unknown",
                            "message": error["msg"],
                            "value": error.get("input", "not provided")
                        }
                        for error in e.errors()
                    ]
                }
            )
        except Exception as e:
            self.error_count += 1
            return MCPError(
                code=MCPErrorCode.INTERNAL_ERROR.value,
                message="Internal error during request validation",
                data={"details": str(e)}
            )
    
    def create_response(self, request_id: Optional[Union[str, int]], 
                       result: Any = None, error: Optional[MCPError] = None) -> str:
        """Create MCP response message"""
        try:
            if error:
                response = MCPResponse(
                    id=request_id,
                    error={
                        "code": error.code,
                        "message": error.message,
                        "data": error.data
                    }
                )
            else:
                response = MCPResponse(
                    id=request_id,
                    result=result
                )
            
            response_json = response.model_dump_json(exclude_none=True)
            
            # Store response in history
            self.message_history.append(response)
            if len(self.message_history) > 100:
                self.message_history.pop(0)
            
            return response_json
            
        except Exception as e:
            # Fallback error response
            self.error_count += 1
            error_response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": MCPErrorCode.INTERNAL_ERROR.value,
                    "message": "Internal error creating response",
                    "data": {"details": str(e)}
                }
            }
            return json.dumps(error_response)
    
    def create_notification(self, method: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Create MCP notification message (no response expected)"""
        try:
            notification = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params or {}
            }
            
            # Validate notification method
            if method not in self.supported_methods:
                logger.warning(f"Creating notification for unsupported method: {method}")
            
            return json.dumps(notification, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return json.dumps({
                "jsonrpc": "2.0",
                "method": "error",
                "params": {"error": str(e)}
            })
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get protocol handler statistics"""
        return {
            "total_messages": len(self.message_history),
            "error_count": self.error_count,
            "supported_methods": len(self.supported_methods),
            "success_rate": max(0, (len(self.message_history) - self.error_count) / max(1, len(self.message_history)))
        }

# Global protocol handler instance
protocol_handler = MCPProtocolHandler()
