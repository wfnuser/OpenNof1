# API Contracts: User Custom Prompt System

**Phase**: 1 (Design) | **Date**: 2025-11-13 | **Feature**: Custom Prompt System

## REST API Endpoints

Base URL: `http://localhost:8000` (development)

### Authentication
No authentication required (single-user system)

### Content Type
All endpoints accept and return `application/json`

### Error Response Format
```json
{
  "detail": "Error description",
  "status_code": 400
}
```

## Endpoints

### 1. List Custom Prompts

**Endpoint**: `GET /prompts`  
**Purpose**: Retrieve all custom prompts

**Request**:
- **Method**: GET
- **Headers**: `Content-Type: application/json`
- **Body**: None
- **Query Parameters**: None

**Response**:
```json
{
  "prompts": [
    {
      "id": 1,
      "title": "Conservative Trading Analysis",
      "content": "Focus on risk management and conservative entry points...",
      "prompt_type": "analysis",
      "is_active": true,
      "created_at": "2025-11-13T10:30:00Z",
      "updated_at": "2025-11-13T10:30:00Z"
    },
    {
      "id": 2,
      "title": "Aggressive Growth Strategy",
      "content": "Look for high-growth opportunities with higher risk tolerance...",
      "prompt_type": "analysis",
      "is_active": false,
      "created_at": "2025-11-13T11:00:00Z",
      "updated_at": "2025-11-13T11:00:00Z"
    }
  ],
  "total": 2
}
```

**Status Codes**:
- `200 OK`: Successfully retrieved prompts
- `500 Internal Server Error`: Database error

---

### 2. Create Custom Prompt

**Endpoint**: `POST /prompts`  
**Purpose**: Create a new custom prompt

**Request**:
- **Method**: POST
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
  "title": "Custom Strategy Name",
  "content": "Your custom prompt content here. Focus on specific analysis criteria and trading approach.",
  "prompt_type": "analysis"
}
```

**Response**:
```json
{
  "id": 3,
  "title": "Custom Strategy Name",
  "content": "Your custom prompt content here. Focus on specific analysis criteria and trading approach.",
  "prompt_type": "analysis",
  "is_active": false,
  "created_at": "2025-11-13T12:00:00Z",
  "updated_at": "2025-11-13T12:00:00Z"
}
```

**Validation Rules**:
- `title`: Required, max 100 characters, non-empty after trim
- `content`: Required, non-empty after trim
- `prompt_type`: Optional, defaults to "analysis", must be one of ["analysis", "system", "decision"]

**Status Codes**:
- `201 Created`: Prompt successfully created
- `400 Bad Request`: Validation error
- `500 Internal Server Error`: Database error

---

### 3. Get Specific Prompt

**Endpoint**: `GET /prompts/{id}`  
**Purpose**: Retrieve a specific custom prompt by ID

**Request**:
- **Method**: GET
- **Headers**: `Content-Type: application/json`
- **Path Parameters**: 
  - `id` (integer): The prompt ID
- **Body**: None

**Response**:
```json
{
  "id": 1,
  "title": "Conservative Trading Analysis",
  "content": "Focus on risk management and conservative entry points...",
  "prompt_type": "analysis",
  "is_active": true,
  "created_at": "2025-11-13T10:30:00Z",
  "updated_at": "2025-11-13T10:30:00Z"
}
```

**Status Codes**:
- `200 OK`: Successfully retrieved prompt
- `404 Not Found`: Prompt with given ID not found
- `500 Internal Server Error`: Database error

---

### 4. Activate/Deactivate Prompt

**Endpoint**: `PUT /prompts/{id}/activate`  
**Purpose**: Set a prompt as active (deactivates other prompts of same type)

**Request**:
- **Method**: PUT
- **Headers**: `Content-Type: application/json`
- **Path Parameters**: 
  - `id` (integer): The prompt ID to activate
- **Body**:
```json
{
  "is_active": true
}
```

**Response**:
```json
{
  "id": 1,
  "title": "Conservative Trading Analysis",
  "content": "Focus on risk management and conservative entry points...",
  "prompt_type": "analysis",
  "is_active": true,
  "created_at": "2025-11-13T10:30:00Z",
  "updated_at": "2025-11-13T12:15:00Z"
}
```

**Business Logic**:
- When setting `is_active: true`, all other prompts of the same `prompt_type` are automatically set to `is_active: false`
- When setting `is_active: false`, the system falls back to default system prompts
- Operation is atomic (database transaction)

**Status Codes**:
- `200 OK`: Successfully updated prompt activation status
- `404 Not Found`: Prompt with given ID not found
- `500 Internal Server Error`: Database error

---

### 5. Delete Custom Prompt

**Endpoint**: `DELETE /prompts/{id}`  
**Purpose**: Permanently delete a custom prompt

**Request**:
- **Method**: DELETE
- **Headers**: `Content-Type: application/json`
- **Path Parameters**: 
  - `id` (integer): The prompt ID to delete
- **Body**: None

**Response**:
```json
{
  "message": "Prompt deleted successfully",
  "deleted_id": 1
}
```

**Business Logic**:
- If deleted prompt was active, system automatically falls back to default prompts
- Deletion is permanent and cannot be undone
- Active analyses using the prompt will complete with the prompt, future analyses use default

**Status Codes**:
- `200 OK`: Successfully deleted prompt
- `404 Not Found`: Prompt with given ID not found
- `500 Internal Server Error`: Database error

---

### 6. Get Active Prompt

**Endpoint**: `GET /prompts/active/{type}`  
**Purpose**: Get the currently active prompt for a specific type

**Request**:
- **Method**: GET
- **Headers**: `Content-Type: application/json`
- **Path Parameters**: 
  - `type` (string): The prompt type ("analysis", "system", "decision")
- **Body**: None

**Response**:
```json
{
  "id": 1,
  "title": "Conservative Trading Analysis",
  "content": "Focus on risk management and conservative entry points...",
  "prompt_type": "analysis",
  "is_active": true,
  "created_at": "2025-11-13T10:30:00Z",
  "updated_at": "2025-11-13T10:30:00Z"
}
```

**Response (No Active Custom Prompt)**:
```json
{
  "message": "No active custom prompt for type 'analysis', using system default",
  "prompt_type": "analysis",
  "using_default": true
}
```

**Status Codes**:
- `200 OK`: Successfully retrieved active prompt or default notification
- `400 Bad Request`: Invalid prompt type
- `500 Internal Server Error`: Database error

## Error Codes

### Validation Errors (400 Bad Request)

```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "ensure this value has at most 100 characters",
      "type": "value_error.any_str.max_length",
      "ctx": {"limit_value": 100}
    }
  ],
  "status_code": 400
}
```

### Not Found Errors (404 Not Found)

```json
{
  "detail": "Prompt with id 999 not found",
  "status_code": 404
}
```

### Internal Server Errors (500 Internal Server Error)

```json
{
  "detail": "Internal server error occurred while processing request",
  "status_code": 500
}
```

## Integration Points

### Frontend Integration

**JavaScript API Client**:
```javascript
// Frontend API methods (add to /frontend/src/lib/api.ts)

export const promptsApi = {
  // Get all prompts
  getAll: async () => {
    const response = await fetch(`${API_BASE}/prompts`);
    return response.json();
  },

  // Create new prompt
  create: async (prompt) => {
    const response = await fetch(`${API_BASE}/prompts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(prompt),
    });
    return response.json();
  },

  // Get specific prompt
  getById: async (id) => {
    const response = await fetch(`${API_BASE}/prompts/${id}`);
    return response.json();
  },

  // Activate/deactivate prompt
  activate: async (id, isActive) => {
    const response = await fetch(`${API_BASE}/prompts/${id}/activate`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_active: isActive }),
    });
    return response.json();
  },

  // Delete prompt
  delete: async (id) => {
    const response = await fetch(`${API_BASE}/prompts/${id}`, {
      method: 'DELETE',
    });
    return response.json();
  },

  // Get active prompt by type
  getActive: async (type) => {
    const response = await fetch(`${API_BASE}/prompts/active/${type}`);
    return response.json();
  },
};
```

### Backend Service Integration

The API endpoints will be implemented in `/backend/api/routes.py` and will use a `PromptService` class for business logic.

**Service Interface**:
```python
class PromptService:
    async def get_all_prompts() -> List[CustomPromptResponse]
    async def create_prompt(prompt_data: CustomPromptCreate) -> CustomPromptResponse
    async def get_prompt_by_id(prompt_id: int) -> CustomPromptResponse
    async def activate_prompt(prompt_id: int, is_active: bool) -> CustomPromptResponse
    async def delete_prompt(prompt_id: int) -> bool
    async def get_active_prompt(prompt_type: str) -> Optional[CustomPromptResponse]
```

### Agent Integration

The active prompts will be consumed by the agent workflow in `/backend/agent/nodes/analysis_node.py`:

```python
# Integration point in analysis workflow
async def get_analysis_prompt() -> str:
    active_prompt = await prompt_service.get_active_prompt("analysis")
    if active_prompt:
        return active_prompt.content
    else:
        return get_default_system_prompt()  # Fallback to system default
```

## Testing Contract

### Unit Test Coverage
- All endpoint request/response validation
- Error handling for invalid inputs
- Business logic for prompt activation/deactivation
- Database integration tests

### Integration Test Coverage  
- End-to-end API workflows (create → activate → use in analysis)
- Frontend-backend integration
- Database transaction integrity
- Cache invalidation on updates

### Performance Testing
- Response times <100ms for all endpoints
- Concurrent request handling
- Database query optimization validation