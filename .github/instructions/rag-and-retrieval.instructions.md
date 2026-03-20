# RAG And Retrieval Instructions

Use this file when adding or updating workflow docs, instructions, prompts, or context artifacts that should be easy for agents and humans to retrieve.

## Goals
- Make the current source of truth obvious.
- Minimize duplicated guidance across files.
- Keep retrieval targeted so agents do not need broad exploratory scans for routine questions.

## Rules
- Treat `.github/CONTEXT.md` as the authoritative current-state file.
- Treat `.github/PLAN.md` as the current task-spec artifact, not a permanent architecture document.
- Treat `.github/WORKFLOW.md` as the orchestration file for role selection and handoffs.
- Treat `.github/RAG-INDEX.md` as the router that points to authoritative files.
- Prefer linking or pointing to an existing authoritative file instead of copying the same rule into multiple documents.

## Authoring Guidelines
- Use stable, descriptive file names for instructions and workflow docs.
- Start each document with a one-line purpose statement.
- Use consistent section names for searchability, such as `Source Of Truth`, `Workflow`, `Validation`, `Common Questions`, and `Rules`.
- Keep examples concrete and repo-specific.
- When a new doc becomes authoritative for a topic, add it to `.github/RAG-INDEX.md`.

## Update Triggers
- New agent role or workflow handoff
- New instruction file
- New recurring gotcha or debugging pattern
- Major architectural decision that changes where truth lives
- New prompt template intended for repeated use

## Anti-Patterns
- Duplicating architecture decisions across multiple files and letting them drift
- Leaving placeholder workflow docs that agents cannot use operationally
- Adding a new instruction file without updating `.github/RAG-INDEX.md`
- Putting current-state decisions in prompt templates instead of `.github/CONTEXT.md`

## Validation
- Confirm every new workflow or instruction file is referenced from `.github/RAG-INDEX.md`.
- Confirm the file points to existing paths only.
- Confirm no duplicated rule is more detailed than the true authoritative source.
