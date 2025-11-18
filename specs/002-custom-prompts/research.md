# Research Report: User Custom Prompt System

**Phase**: 0 (Research) | **Date**: 2025-11-13 | **Feature**: Custom Prompt System

## Research Findings

### Database Schema Design

**Decision**: Create new CustomPrompt table instead of extending SystemConfig  
**Rationale**: 
- SystemConfig is designed for simple key-value pairs; custom prompts need structured data (title, content, timestamps, metadata)
- Separate table provides better data integrity and query performance
- Enables future enhancements like prompt versioning, sharing, and analytics

**Alternatives considered**:
- Extending SystemConfig with JSON storage: Rejected due to poor query performance and validation complexity
- File-based storage: Rejected due to constitutional requirement for SQLite simplicity

### Prompt Integration Architecture

**Decision**: Inject custom prompts into existing LangGraph workflow via prompt template system  
**Rationale**:
- Preserves existing agent workflow structure
- Maintains constitutional agent-first architecture  
- Enables runtime prompt switching without system restart
- Leverages existing LangChain prompt template capabilities

**Alternatives considered**:
- Rebuilding agent workflow: Rejected due to high complexity and risk
- Static prompt replacement in config files: Rejected due to lack of user-specific customization

### Frontend Integration Pattern  

**Decision**: Add settings page with prompt management interface, not in-dashboard editing  
**Rationale**:
- Separates configuration concerns from trading dashboard
- Prevents accidental prompt changes during active trading
- Provides dedicated space for prompt management features
- Aligns with existing single-page app architecture

**Alternatives considered**:
- Modal-based editing: Rejected due to screen space limitations for prompt editing
- Inline dashboard editing: Rejected due to constitutional profit-first principle (avoid disrupting trading focus)

### Database Migration Strategy

**Decision**: Use Alembic migration with backward-compatible schema changes  
**Rationale**:
- Maintains existing database integrity
- Enables rollback capability
- Follows existing project migration patterns
- Constitutional SQLite simplicity compliance

**Implementation**:
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

CREATE INDEX idx_custom_prompts_active ON custom_prompts(is_active);
CREATE INDEX idx_custom_prompts_type ON custom_prompts(prompt_type);
```

### API Design Pattern

**Decision**: RESTful endpoints following existing FastAPI patterns  
**Rationale**:
- Consistency with existing `/analysis`, `/config` endpoints
- Leverages existing error handling and validation
- Simple CRUD operations align with feature requirements
- Maintains constitutional API design principles

**Endpoints**:
- `GET /prompts` - List all custom prompts
- `POST /prompts` - Create new custom prompt  
- `GET /prompts/{id}` - Get specific prompt
- `PUT /prompts/{id}/activate` - Set prompt as active
- `DELETE /prompts/{id}` - Delete prompt

### Prompt Validation Strategy

**Decision**: Multi-layer validation (client, API, agent runtime)  
**Rationale**:
- Prevents malformed prompts from breaking analysis
- Satisfies constitutional requirement for system reliability
- Provides immediate user feedback
- Constitutional profit-first principle (prevent trading disruption)

**Validation layers**:
1. Frontend: Basic syntax and length validation
2. API: Pydantic model validation and content sanitization  
3. Agent: Runtime prompt execution validation with fallback to system prompt

### Performance Optimization

**Decision**: In-memory prompt caching with database persistence  
**Rationale**:
- Meets <100ms retrieval performance goal
- Reduces database load during analysis cycles
- Maintains constitutional SQLite simplicity
- Cache invalidation on prompt updates ensures consistency

**Implementation**: Simple dict-based cache in prompt service with TTL refresh

### Error Handling Strategy

**Decision**: Graceful degradation to system prompts on custom prompt failure  
**Rationale**:
- Constitutional profit-first principle: never stop trading due to prompt issues
- Maintains 99.9% uptime requirement
- Provides clear error feedback without system disruption
- Agent-first architecture: agent continues operation with fallback

### Testing Strategy

**Decision**: Unit tests for prompt service, integration tests for agent workflow  
**Rationale**:
- Validates prompt CRUD operations independently
- Ensures agent workflow integration doesn't break existing functionality
- Aligns with existing pytest testing patterns
- Constitutional requirement for system reliability

## Technical Decisions Summary

1. **Database**: New CustomPrompt table with SQLite + Alembic
2. **Backend**: Prompt service layer + FastAPI REST endpoints  
3. **Agent Integration**: LangChain template injection in analysis node
4. **Frontend**: Dedicated settings page with React components
5. **Performance**: In-memory caching + database persistence
6. **Validation**: Multi-layer with graceful degradation
7. **Testing**: Unit + integration test coverage

All decisions align with constitutional principles and technical constraints. No additional research required - ready for Phase 1 design.