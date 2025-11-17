# Tasks: User Custom Prompt System

**Input**: Design documents from `/specs/002-custom-prompts/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/` for Python FastAPI, `frontend/` for React/Next.js
- Extending existing project structure per plan.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and database preparation

- [ ] T001 Create database migration for custom_prompts table in backend/database/migrations/
- [ ] T002 [P] Add CustomPrompt SQLAlchemy model to backend/database/models.py
- [ ] T003 [P] Add Pydantic schemas for CustomPrompt in backend/services/prompt_service.py
- [ ] T004 [P] Apply database migration using alembic upgrade head

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core prompt service infrastructure that MUST be complete before user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create PromptService class in backend/services/prompt_service.py
- [ ] T006 [P] Implement caching layer for active prompts in backend/services/prompt_service.py
- [ ] T007 [P] Add prompt validation methods to PromptService
- [ ] T008 Add prompt management endpoints structure to backend/api/routes.py
- [ ] T009 [P] Create base prompt API integration methods in frontend/src/lib/api.ts

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Create Custom Analysis Prompts (Priority: P1) 🎯 MVP

**Goal**: Users can create custom prompts to personalize AI agent analysis and use them instead of system defaults

**Independent Test**: Create a custom prompt via the UI, save it, verify it appears in the prompt library, activate it, and confirm the AI agent uses it during analysis

### Implementation for User Story 1

- [ ] T010 [P] [US1] Implement POST /prompts endpoint in backend/api/routes.py
- [ ] T011 [P] [US1] Implement GET /prompts endpoint in backend/api/routes.py  
- [ ] T012 [P] [US1] Implement GET /prompts/{id} endpoint in backend/api/routes.py
- [ ] T013 [P] [US1] Implement PUT /prompts/{id}/activate endpoint in backend/api/routes.py
- [ ] T014 [P] [US1] Implement DELETE /prompts/{id} endpoint in backend/api/routes.py
- [ ] T015 [P] [US1] Implement GET /prompts/active/{type} endpoint in backend/api/routes.py
- [ ] T016 [US1] Implement PromptService.get_all_prompts method in backend/services/prompt_service.py
- [ ] T017 [US1] Implement PromptService.create_prompt method in backend/services/prompt_service.py
- [ ] T018 [US1] Implement PromptService.get_prompt_by_id method in backend/services/prompt_service.py
- [ ] T019 [US1] Implement PromptService.activate_prompt method in backend/services/prompt_service.py
- [ ] T020 [US1] Implement PromptService.delete_prompt method in backend/services/prompt_service.py
- [ ] T021 [US1] Implement PromptService.get_active_prompt method in backend/services/prompt_service.py
- [ ] T022 [US1] Modify analysis_node.py to use custom prompts in backend/agent/nodes/analysis_node.py
- [ ] T023 [US1] Add prompt selection to agent state in backend/agent/state.py
- [ ] T024 [P] [US1] Create PromptEditor component in frontend/src/components/prompts/PromptEditor.tsx
- [ ] T025 [P] [US1] Create PromptList component in frontend/src/components/prompts/PromptList.tsx
- [ ] T026 [P] [US1] Create PromptSelector component in frontend/src/components/prompts/PromptSelector.tsx
- [ ] T027 [US1] Create Settings page in frontend/src/app/settings/page.tsx
- [ ] T028 [US1] Implement prompt API methods in frontend/src/lib/api.ts
- [ ] T029 [US1] Add navigation link to Settings page in frontend/src/components/
- [ ] T030 [US1] Add graceful fallback to system prompts on custom prompt failure
- [ ] T031 [US1] Add prompt validation and error handling across all layers

**Checkpoint**: At this point, User Story 1 should be fully functional - users can create, manage, activate custom prompts and the AI agent uses them for analysis

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Improvements and validation across the complete feature

- [ ] T032 [P] Add comprehensive error handling and user feedback for prompt operations
- [ ] T033 [P] Optimize prompt caching and database query performance
- [ ] T034 [P] Add prompt content validation to prevent malformed input
- [ ] T035 [P] Add loading states and optimistic UI updates to frontend
- [ ] T036 [P] Validate quickstart.md by following setup instructions end-to-end
- [ ] T037 [P] Add logging for prompt operations and agent workflow integration
- [ ] T038 Run complete system test: create prompt → activate → trigger analysis → verify custom prompt usage

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS user story implementation
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **Polish (Phase 4)**: Depends on User Story 1 completion

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **Independent Implementation**: This feature has only one user story, making implementation straightforward

### Within User Story 1

- API endpoints (T010-T015) can run in parallel
- Service methods (T016-T021) must follow after their corresponding endpoints
- Agent integration (T022-T023) depends on service methods completion
- Frontend components (T024-T026) can run in parallel
- Settings page and API integration (T027-T029) tie components together
- Final validation and error handling (T030-T031) complete the story

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- API endpoints T010-T015 can be implemented in parallel
- Frontend components T024-T026 can be developed in parallel
- All Polish tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all API endpoints together:
Task: "Implement POST /prompts endpoint in backend/api/routes.py"
Task: "Implement GET /prompts endpoint in backend/api/routes.py"
Task: "Implement GET /prompts/{id} endpoint in backend/api/routes.py"
Task: "Implement PUT /prompts/{id}/activate endpoint in backend/api/routes.py"
Task: "Implement DELETE /prompts/{id} endpoint in backend/api/routes.py"
Task: "Implement GET /prompts/active/{type} endpoint in backend/api/routes.py"

# Launch all frontend components together:
Task: "Create PromptEditor component in frontend/src/components/prompts/PromptEditor.tsx"
Task: "Create PromptList component in frontend/src/components/prompts/PromptList.tsx"  
Task: "Create PromptSelector component in frontend/src/components/prompts/PromptSelector.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (database migration and models)
2. Complete Phase 2: Foundational (core prompt service infrastructure)
3. Complete Phase 3: User Story 1 (complete custom prompt functionality)
4. **STOP and VALIDATE**: Test User Story 1 independently using quickstart.md
5. Ready for production deployment

### Incremental Delivery

1. Complete Setup + Foundational → Database and service layer ready
2. Add Backend API → Prompt CRUD operations available
3. Add Frontend UI → Users can manage prompts via interface  
4. Add Agent Integration → Custom prompts used in AI analysis
5. Add Polish → Production-ready system with error handling and optimization

### Single Developer Strategy

Recommended sequence for single developer:
1. Database setup and models (T001-T004)
2. Core service infrastructure (T005-T009)  
3. Backend API implementation (T010-T021)
4. Agent workflow integration (T022-T023)
5. Frontend components and integration (T024-T031)
6. Polish and validation (T032-T038)

---

## Notes

- [P] tasks = different files, no dependencies
- [US1] label maps all tasks to the single user story
- User Story 1 delivers complete MVP functionality
- Each checkpoint allows for independent testing and validation
- Focus on graceful fallback to system prompts ensures trading operations continue even if custom prompts fail
- Commit after each task or logical group for easy rollback if needed