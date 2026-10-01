# Architectural Guidelines Summary Reference

This document summarizes the core enterprise guidelines provided by `gea-agents-arch-guidelines-mcp-server`:

## 📚 Guideline Directory

### [DOC-01] AI Agent Quality Engineering
- **Domain**: Quality, Observability & Reliability
- **Summary**: Systematic evaluation, observability, cost & security engineering for enterprise agents on Google Cloud.
- **Key Concepts**: Automated evaluation harnesses, OpenTelemetry distributed tracing, token budget enforcement, regression testing.

### [DOC-02] Vibe Coding Agent Security & Evaluation
- **Domain**: Security & Sandboxing
- **Summary**: Sandboxing, Zero Ambient Authority (ZAA), Agentic SecOps & session convergence in coding environments.
- **Key Concepts**: Zero Ambient Authority (ZAA), least privilege credential minting, non-root container isolation, hermetic execution environments.

### [DOC-03] Open AI Agent Protocol Stack
- **Domain**: Protocol Layering & Agent Interoperability
- **Summary**: Comprehensive protocol architecture spanning MCP, A2A, UCP, AP2/x402, and A2UI.
- **Key Concepts**:
  - **A2UI**: Declarative, non-executable JSON component definitions rendered natively by client design systems. Prevents XSS and prompt injection code execution.
  - **MCP (Model Context Protocol)**: Exposing databases, tools, and knowledge graphs to agents.
  - **A2A**: Agent-to-Agent communication contracts and context-scoped task delegation.
  - **Layer Separation**: Tool execution, agent orchestration, and presentation logic must never be conflated.

### [DOC-08] Context Engineering for Stateful AI Agents
- **Domain**: Context & Memory Management
- **Summary**: Sessions, Memory Banks, RAG architectures, and state governance on Google Cloud.
- **Key Concepts**: Progressive disclosure, working context vs persistent memory, semantic recall, context window protection.

### [DOC-09] Platform-Native State Management
- **Domain**: Runtime State & Persistence
- **Summary**: State management with Gemini Enterprise Agent Runtime & Memory Bank vs self-hosted state stores.
- **Key Concepts**: Google Cloud Spanner Graph ISO GQL property graphs, BigQuery analytics, high-availability multi-region persistence.
