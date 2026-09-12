# Cognition Workload

This directory defines the **Cognition** layer of the AI stack, focusing on the "thinking" and "reasoning" processes of the system. While the `llm` workload handles the raw model execution, `cognition` manages how those models are orchestrated to solve complex tasks.

## Overview

The Cognition workload is responsible for transforming raw LLM outputs into structured reasoning, memory management, and autonomous agent loops.

### Core Components

- **Reasoning Loops**: Implementation of patterns like Chain-of-Thought (CoT) or ReAct.
- **State Management**: Tracking the "mental state" of an agent across multiple turns.
- **Cognitive Architectures**: Definitions for how the system moves from perception $\rightarrow$ reasoning $\rightarrow$ action.

## Workflow

1. **Input**: A prompt or trigger from a `bridge` (e.g., bluetooth or zigbee).
2. **Processing**: The cognition engine uses an LLM to determine the intent.
3. **Iteration**: Recursive refinement of the thought process until a conclusion is reached.
4. **Output**: A structured command sent to a `workload` or `appliance`.

## Integration

This workload interacts closely with:
- `/logical/appliances/ai/llm`: The underlying model providers.
- `/logical/workloads/ai/rlm`: The Reflection/Refinement loop.
- `/logical/workloads/bluetooth`: Providing the sensory input for cognitive processing.

## Future Tasks
- [ ] Implement a state-machine for complex reasoning paths.
- [ ] Integrate a vector database for long-term cognitive memory.
- [ ] Define a standard schema for "Cognitive Artifacts".
