# Implementation Plan: User Custom Prompt System

**Branch**: `002-custom-prompts` | **Date**: 2025-11-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-custom-prompts/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement a custom prompt system that allows users to create and use personalized prompts for AI analysis instead of relying solely on system defaults. The feature will integrate with the existing LangGraph agent workflow, SQLite database, and FastAPI backend, adding prompt management capabilities to both the Python backend and React frontend. Users will be able to create custom prompts via a new configuration interface, and the AI agent will use the selected custom prompt during market analysis operations.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript/React (frontend)  
**Primary Dependencies**: FastAPI 0.104.0, LangChain, LangGraph, SQLAlchemy 2.0, Next.js 14, Tailwind CSS  
**Storage**: SQLite with Alembic migrations, extending existing SystemConfig table or new CustomPrompt table  
**Testing**: pytest (backend), Jest/React Testing Library (frontend)  
**Target Platform**: Linux/macOS server + web browser (existing web application)
**Project Type**: Web application (extending existing full-stack system)  
**Performance Goals**: <100ms prompt retrieval, seamless integration with existing 180s analysis cycle  
**Constraints**: Must not disrupt existing trading operations, maintain 99.9% uptime during prompt changes  
**Scale/Scope**: Single user initially, 50+ custom prompts per user, extend 5 existing files, add 3 new endpoints

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ I. Agent-First Architecture
- **Compliance**: Custom prompts enhance Agent decision-making autonomy by allowing users to specify analysis strategies
- **Implementation**: Prompts integrate into existing LangGraph workflow without changing agent autonomy boundaries

### ✅ II. Python AI Ecosystem Integration  
- **Compliance**: Uses existing LangChain/LangGraph infrastructure with no new AI dependencies
- **Implementation**: Leverages current OpenAI-compatible API with prompt template system

### ✅ III. File-Based Configuration Management
- **Compliance**: Custom prompts stored in database for user-specific data, system prompts remain in YAML
- **Implementation**: Extends existing config system without replacing file-based system configuration

### ✅ IV. User Profit-First Design
- **Compliance**: Directly enhances trading performance by allowing strategy-specific analysis prompts
- **Implementation**: Users can optimize AI analysis for their specific trading approaches and market conditions

### ✅ V. Extensible Tools & MCP Future-Proofing
- **Compliance**: Implements standardized prompt interface that can accommodate future MCP prompt tools
- **Implementation**: Clean separation between prompt storage, selection, and execution

### ✅ VI. SQLite Simplicity
- **Compliance**: Uses existing SQLite database with simple schema extension
- **Implementation**: Single table addition with clear migration path

**Constitutional Status**: ✅ PASSED - All principles aligned, no violations requiring justification

### Post-Phase 1 Constitutional Re-Check ✅

After completing detailed design (data model, API contracts, quickstart):

- **✅ Agent-First Architecture**: Confirmed - custom prompts enhance agent decision-making through LangChain template integration without compromising agent autonomy
- **✅ Python AI Ecosystem**: Confirmed - leverages existing LangChain/LangGraph infrastructure with no additional AI dependencies  
- **✅ File-Based Config**: Confirmed - system prompts remain in YAML, user-specific prompts appropriately stored in database
- **✅ User Profit-First**: Confirmed - direct trading performance enhancement through personalized analysis strategies
- **✅ Extensible Tools**: Confirmed - clean prompt service interface enables future MCP integration
- **✅ SQLite Simplicity**: Confirmed - single table addition with proper migrations and indexing

**Final Status**: All constitutional principles maintained through detailed design phase.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── database/
│   ├── models.py              # Add CustomPrompt model
│   └── migrations/            # Add custom prompt table migration
├── api/
│   └── routes.py              # Add /prompts endpoints
├── agent/
│   ├── nodes/
│   │   └── analysis_node.py   # Modify to use custom prompts
│   └── state.py               # Add prompt selection to state
├── config/
│   └── agent_config.py        # Extend for prompt configuration
└── services/                  # NEW: Prompt management service
    └── prompt_service.py

frontend/
├── src/
│   ├── components/
│   │   ├── prompts/           # NEW: Prompt management components
│   │   │   ├── PromptEditor.tsx
│   │   │   ├── PromptList.tsx
│   │   │   └── PromptSelector.tsx
│   │   └── ui/                # Extend existing UI components
│   ├── pages/                 # Add configuration page
│   │   └── settings.tsx       # NEW: Settings page
│   └── lib/
│       └── api.ts             # Add prompt API methods
└── tests/
    └── components/            # Component tests for new UI
```

**Structure Decision**: Extending existing web application structure. Backend adds prompt management service and database models, frontend adds configuration interface. Minimal structural changes leverage existing FastAPI backend and React frontend architecture.

## Complexity Tracking

No violations to track - all constitutional principles satisfied.
