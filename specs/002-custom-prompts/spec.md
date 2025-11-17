# Feature Specification: User Custom Prompt System

**Feature Branch**: `002-custom-prompts`  
**Created**: 2025-11-13  
**Status**: Draft  
**Input**: User description: "我们现在准备实现一个系统，希望它可以有用户自定义 prompt 的能力。先帮我规划一下，有可能有哪些改动需要做。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create Custom Analysis Prompts (Priority: P1)

Users can create custom prompts to personalize how the AI agent analyzes trading data and market conditions, allowing them to focus on specific indicators or strategies that matter to their trading approach.

**Why this priority**: Core functionality that delivers immediate value - users can start customizing their analysis immediately with just basic prompt creation capability.

**Independent Test**: Can be fully tested by creating a custom prompt, saving it, and verifying it appears in the prompt library, delivering immediate personalization value.

**Acceptance Scenarios**:

1. **Given** a user is on the analysis configuration page, **When** they enter a custom prompt for market analysis, **Then** the system saves the prompt and makes it available for use
2. **Given** a user has created a custom prompt, **When** they trigger an analysis, **Then** the system uses their custom prompt instead of the default

---


### Edge Cases

- What happens when a custom prompt contains invalid formatting or syntax that could break the AI analysis?
- How does the system handle empty or whitespace-only prompts?
- What occurs when a user creates multiple prompts with the same name?
- How does the system respond when the selected custom prompt fails during analysis execution?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to create new custom prompts with a title and content
- **FR-002**: System MUST save custom prompts persistently for each user
- **FR-003**: System MUST allow users to select which custom prompt to use for analysis operations
- **FR-004**: System MUST provide a default fallback prompt when no custom prompt is selected
- **FR-007**: System MUST validate prompt content to prevent system errors during analysis
- **FR-008**: System MUST display a list of all custom prompts for each user
- **FR-009**: System MUST support prompts without character limits to allow maximum flexibility
- **FR-010**: System MUST allow all users to create and view custom prompts without role restrictions
- **FR-011**: System MUST distinguish between system-provided prompts and user-created custom prompts
- **FR-012**: System MUST clearly identify prompt source (system vs. user) in the prompt selection interface

### Key Entities

- **Custom Prompt**: Represents a user-defined text template for AI analysis, containing title, content, creation date, and user ownership
- **System Prompt**: Represents built-in prompts provided by the system for standard analysis operations

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create and save a custom prompt in under 3 minutes
- **SC-002**: Custom prompts are successfully applied to analysis operations with 99.9% reliability
- **SC-003**: Users can view and select their custom prompts with 100% accuracy
- **SC-004**: System supports at least 50 custom prompts per user without performance degradation
- **SC-005**: 80% of users who create custom prompts continue to use the feature after one week
- **SC-006**: Prompt validation prevents 100% of system crashes due to malformed prompt content