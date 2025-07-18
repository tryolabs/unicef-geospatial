# UNICEF Geosphere API Documentation

This document provides comprehensive API documentation for the UNICEF Geosphere project, covering all endpoints, data formats, and integration patterns.

## Overview

The UNICEF Geosphere project exposes APIs at multiple levels:

1. **Frontend API**: User-facing HTTP endpoints for the chat interface
2. **Agent API**: Core orchestration service with LLM capabilities
3. **MCP APIs**: Model Context Protocol servers for specialized data access

## Architecture Overview

```
┌─────────────────┐   HTTP/WebSocket   ┌─────────────────┐   MCP Protocol   ┌─────────────────┐
│   Frontend      │────────────────────│   Agent API     │──────────────────│ MCP Servers     │
│   (React)       │                    │   (FastAPI)     │                  │ (FastMCP)       │
└─────────────────┘                    └─────────────────┘                  └─────────────────┘
                                                │
                                                ├─── Data Warehouse MCP (Port 8001)
                                                ├─── RAG MCP (Port 8002)
                                                └─── GEE MCP (Port 8003)
```

## Agent API (Port 8000)

The main API service that orchestrates all interactions between the frontend and MCP servers.

### Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com/api`

### Authentication

The API uses JWT-based authentication with the following flow:

#### 1. Obtain Access Token

**Endpoint**: `POST /token`

**Content-Type**: `application/x-www-form-urlencoded`

**Request**:

```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_username&password=your_password"
```

**Response**:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "username": "your_username"
}
```

**Error Responses**:

```json
// Invalid credentials
{
  "detail": "Incorrect username or password"
}

// Validation error
{
  "detail": [
    {
      "loc": ["body", "username"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 2. Use Access Token

Include the token in the Authorization header for subsequent requests:

```bash
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Core Endpoints

#### Health Check

**Endpoint**: `GET /`

**Description**: Basic health check endpoint

**Request**:

```bash
curl http://localhost:8000/
```

**Response**:

```json
{
  "message": "Hello World"
}
```

#### Main Chat Endpoint

**Endpoint**: `POST /api/ask`

**Description**: Submit questions and receive streaming AI responses

**Authentication**: Required

**Content-Type**: `application/json`

**Request Schema**:

```typescript
interface ChatRequest {
  chat_messages: Message[];
  session_id: string;
}

interface Message {
  content: string;
  role: "user" | "assistant";
  trace_id?: string;
  is_thinking?: boolean;
  is_finished?: boolean;
}
```

**Request Example**:

```bash
curl -X POST "http://localhost:8000/api/ask" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_messages": [
      {
        "content": "How many children are at risk of floods in Colombia?",
        "role": "user"
      }
    ],
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**Response Format**: Streaming JSON chunks

The response is delivered as a stream of JSON objects, each representing a different type of update:

#### Response Types

##### 1. Thinking Stream

Provides real-time insight into the AI's reasoning process.

```json
{
  "response": "I'll help you find information about flood risks for children in Colombia. Let me search for relevant data...",
  "is_thinking": true,
  "trace_id": "550e8400-e29b-41d4-a716-446655440001",
  "is_finished": false
}
```

##### 2. Tool Call Information

Shows which backend tools are being executed.

```json
{
  "tool_call": {
    "name": "get_dataset_image_and_metadata",
    "args": {
      "dataset_id": "river_flood"
    }
  },
  "trace_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

##### 3. Final Response

The user-facing answer from the AI.

```json
{
  "response": "Based on the analysis of flood risk data, approximately 2.3 million children in Colombia are exposed to river flood risks...",
  "is_thinking": false,
  "trace_id": "550e8400-e29b-41d4-a716-446655440001",
  "is_finished": true
}
```

##### 4. Map Content

Interactive map HTML for visualization.

```json
{
  "html_content": "<html><head>...</head><body><div id='map'>...</div></body></html>",
  "trace_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

### Error Handling

#### Authentication Errors

```json
{
  "detail": "Could not validate credentials",
  "status_code": 401
}
```

#### Validation Errors

```json
{
  "detail": [
    {
      "loc": ["body", "session_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ],
  "status_code": 422
}
```

#### Server Errors

```json
{
  "detail": "Internal server error occurred while processing request",
  "status_code": 500,
  "trace_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

## MCP Server APIs

The Model Context Protocol servers provide specialized data access through standardized interfaces.

### Available MCP Servers:

- Data Warehouse MCP API (Port 8001)
- RAG MCP API (Port 8002)
- GEE MCP API (Port 8003)

### Common MCP Patterns

All MCP servers follow consistent patterns:

- **Protocol**: Server-Sent Events (SSE) over HTTP
- **Transport**: MCP-compliant messaging
- **Tools**: Exposed as callable functions
- **Responses**: Structured JSON with metadata
