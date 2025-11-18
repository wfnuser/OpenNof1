# Data Model: User Custom Prompt System

**Phase**: 1 (Design) | **Date**: 2025-11-13 | **Feature**: Custom Prompt System

## Entity Definitions

### CustomPrompt

**Purpose**: Represents a user-defined prompt template for AI analysis operations

**Attributes**:
- `id` (Integer, Primary Key): Unique identifier for the prompt
- `title` (String, max 100 chars, required): User-friendly name for the prompt
- `content` (Text, required): The actual prompt text content
- `prompt_type` (String, max 20 chars, default 'analysis'): Type of prompt (analysis, system, decision)
- `is_active` (Boolean, default False): Whether this prompt is currently selected for use
- `created_at` (Timestamp, auto): When the prompt was created
- `updated_at` (Timestamp, auto): When the prompt was last modified

**Validation Rules**:
- `title` must be non-empty and unique per user
- `content` must be non-empty after trimming whitespace
- `prompt_type` must be one of: 'analysis', 'system', 'decision'
- Only one prompt per `prompt_type` can have `is_active = True`

**Relationships**:
- None (single-user system, no user table required)

### SystemPrompt (Existing - for reference)

**Purpose**: Represents built-in prompts provided by the system

**Source**: Configuration file (`/backend/config/agent.yaml`)
**Attributes**:
- `system_prompt` (String): Default system prompt content
- `analysis_templates` (Object): Built-in analysis prompt templates

**Relationship to CustomPrompt**: CustomPrompts can override SystemPrompts when activated

## State Transitions

### CustomPrompt Lifecycle

```
[Created] → [Saved] → [Activated] → [Deactivated] → [Modified] → [Deleted]
           ↗                    ↘                 ↗
     [Validation Failed]    [Active in Use]   [Updated]
```

**State Rules**:
1. **Created**: New prompt validated and saved to database
2. **Activated**: Prompt marked as `is_active = True`, previous active prompt deactivated
3. **Active in Use**: Current analysis operations use this prompt
4. **Deactivated**: Prompt marked as `is_active = False`, system falls back to default
5. **Modified**: Prompt content updated, remains in current activation state
6. **Deleted**: Prompt removed from database, system falls back if was active

### Agent Workflow Integration

```
Analysis Request → Check Active Custom Prompt → Use Custom OR Default → Execute Analysis
                                           ↘                    ↗
                               [No Custom Active]    [Custom Prompt Available]
```

## Database Schema

### SQL Table Definition

```sql
CREATE TABLE custom_prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    prompt_type VARCHAR(20) NOT NULL DEFAULT 'analysis',
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_custom_prompts_active ON custom_prompts(is_active);
CREATE INDEX idx_custom_prompts_type ON custom_prompts(prompt_type);
CREATE UNIQUE INDEX idx_custom_prompts_active_type ON custom_prompts(prompt_type, is_active) 
  WHERE is_active = TRUE;

-- Triggers for updated_at
CREATE TRIGGER update_custom_prompts_updated_at 
  AFTER UPDATE ON custom_prompts
  FOR EACH ROW 
  BEGIN
    UPDATE custom_prompts SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
  END;
```

### Alembic Migration

**Migration File**: `add_custom_prompts_table.py`

```python
"""Add custom prompts table

Revision ID: 002_custom_prompts
Revises: 001_initial
Create Date: 2025-11-13

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table('custom_prompts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('prompt_type', sa.String(length=20), nullable=False, server_default='analysis'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='FALSE'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_custom_prompts_active', 'custom_prompts', ['is_active'])
    op.create_index('idx_custom_prompts_type', 'custom_prompts', ['prompt_type'])
    op.create_index('idx_custom_prompts_active_type', 'custom_prompts', 
                   ['prompt_type', 'is_active'], unique=True, 
                   postgresql_where=sa.text('is_active = TRUE'))

def downgrade():
    op.drop_index('idx_custom_prompts_active_type', 'custom_prompts')
    op.drop_index('idx_custom_prompts_type', 'custom_prompts')
    op.drop_index('idx_custom_prompts_active', 'custom_prompts')
    op.drop_table('custom_prompts')
```

## SQLAlchemy Model

```python
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func
from sqlalchemy.orm import validates
from database.database import Base

class CustomPrompt(Base):
    __tablename__ = "custom_prompts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    prompt_type = Column(String(20), nullable=False, default="analysis")
    is_active = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    @validates('title')
    def validate_title(self, key, title):
        title = title.strip()
        if not title:
            raise ValueError("Title cannot be empty")
        return title

    @validates('content')
    def validate_content(self, key, content):
        content = content.strip()
        if not content:
            raise ValueError("Content cannot be empty")
        return content

    @validates('prompt_type')
    def validate_prompt_type(self, key, prompt_type):
        allowed_types = ['analysis', 'system', 'decision']
        if prompt_type not in allowed_types:
            raise ValueError(f"prompt_type must be one of: {allowed_types}")
        return prompt_type
```

## Pydantic Schemas

```python
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class CustomPromptBase(BaseModel):
    title: str = Field(..., max_length=100, description="User-friendly prompt name")
    content: str = Field(..., description="The prompt text content")
    prompt_type: str = Field(default="analysis", description="Type of prompt")

    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

    @validator('content')
    def content_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()

    @validator('prompt_type')
    def validate_prompt_type(cls, v):
        allowed = ['analysis', 'system', 'decision']
        if v not in allowed:
            raise ValueError(f'prompt_type must be one of: {allowed}')
        return v

class CustomPromptCreate(CustomPromptBase):
    pass

class CustomPromptUpdate(CustomPromptBase):
    title: Optional[str] = Field(None, max_length=100)
    content: Optional[str] = None
    prompt_type: Optional[str] = None

class CustomPromptResponse(CustomPromptBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CustomPromptActivate(BaseModel):
    is_active: bool = Field(..., description="Whether to activate this prompt")
```

## Data Flow

### Prompt Creation Flow

1. **Frontend**: User fills prompt form → validates locally → submits to API
2. **API**: Receives request → validates via Pydantic → calls service
3. **Service**: Validates business rules → saves to database → returns response
4. **Cache**: Updates in-memory cache with new prompt

### Prompt Activation Flow  

1. **Frontend**: User clicks activate → sends PUT request
2. **API**: Validates request → calls service
3. **Service**: 
   - Deactivates current active prompt of same type
   - Activates selected prompt
   - Updates database with transaction
4. **Cache**: Invalidates and refreshes cache
5. **Agent**: Next analysis cycle uses new active prompt

### Analysis Execution Flow

1. **Agent**: Starts analysis → requests active prompt from service
2. **Service**: Checks cache → returns active prompt or falls back to system default
3. **Agent**: Uses prompt in LangChain template → executes analysis
4. **Fallback**: If prompt execution fails → use system prompt → log error

## Performance Considerations

### Caching Strategy
- **Active Prompts**: Cached in memory by prompt_type
- **Cache TTL**: 5 minutes or on update
- **Cache Size**: Minimal (only active prompts)

### Query Optimization
- **Indexes**: On is_active and prompt_type for fast retrieval
- **Connection Pooling**: Use existing SQLAlchemy pool
- **Lazy Loading**: Load prompts only when needed

### Scalability Notes
- **Current Scope**: Single user, ~50 prompts
- **Future Considerations**: Add user_id column when multi-user support needed
- **Database Growth**: Minimal impact with proper indexing