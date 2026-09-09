# DAAOS — Domain-Agnostic Autonomous Orchestration System
# Link for newer code that I will upload after debugging- https://drive.google.com/drive/folders/1-M3HHT6LKkRVJXMp5xniwpGv8_r_lBsT?usp=sharing
## Overview

DAAOS (Domain-Agnostic Autonomous Orchestration System) is an experimental multi-agent orchestration framework designed to coordinate autonomous agents through hierarchical communication, event-driven execution, and dynamic task delegation.

The project aims to evolve beyond traditional multi-agent systems by providing a reusable orchestration runtime capable of supporting different domains, workflows, and agent specializations.

---

## Vision

Most multi-agent systems focus on solving a single workflow.

DAAOS focuses on building the orchestration layer itself.

The long-term goal is to create a runtime where:

* Agents can create new agents.
* Agents can delegate tasks autonomously.
* Communication is hierarchical and scalable.
* Workflows emerge from agent interactions.
* The system remains domain agnostic.

---

## Core Concepts

### Agent Hierarchy

Agents are organized as a tree structure.

```text
Boss
│
├── AgentNode1
│   ├── Leaf1
│   ├── Leaf2
│   └── Leaf3
│
├── AgentNode2
│   ├── Leaf4
│   └── Leaf5
│
└── AgentNode3
```

Each agent may:

* Receive tasks
* Create child agents
* Delegate work
* Communicate with siblings and parents

---

### Event-Driven Communication

Agents communicate through events instead of direct function calls.

Examples:

* TASK_CREATED
* TASK_COMPLETED
* STATUS_UPDATE
* AGENT_SPAWNED

This enables loose coupling and scalable orchestration.

---

### Hierarchical Routing

Communication should remain local whenever possible.

Instead of:

```text
Leaf1 → Boss → Leaf2
```

DAAOS prefers:

```text
Leaf1 → Local Router → Leaf2
```

This reduces communication overhead and improves scalability.

---

### Scheduler-Based Execution

Tasks are managed by a Scheduler rather than directly by the Boss agent.

```text
Boss
 ↓
Scheduler
 ↓
Agents
```

This separation enables future support for:

* dependency management
* workflow orchestration
* parallel execution
* autonomous scheduling

---

## Current Features

### Runtime

* AsyncIO-based execution
* Agent lifecycle management
* Agent registry
* Event routing
* Dynamic agent spawning
* Basic scheduler

### Agent System

* Agent
* AgentNode
* BossAgent
* AgentFactory

### Infrastructure

* Router
* Registry
* Memory
* Task abstraction
* Event abstraction

---

## Project Structure

```text
daaos/

├── main.py
├── agents.py
├── core.py
├── runtime.py
├── registry.py
├── router.py
├── scheduler.py
```

---

## Roadmap

### Phase 1 — Runtime Foundation

* Agent States
* Registry
* Router
* Scheduler

### Phase 2 — Hierarchical Communication

* Parent-child relationships
* Local communication domains
* Hierarchical routing

### Phase 3 — Shared Memory

* Shared memory store
* Context retrieval
* Memory synchronization

### Phase 4 — Dynamic Agent Creation

* Agent spawning by AgentNodes
* Agent lifecycle tracking
* Parent-child management

### Phase 5 — Task Management

* Task identifiers
* Task lifecycle
* Retry policies
* Task tracking

### Phase 6 — Dependency Resolution

* Dependency tracking
* Blocked tasks
* Ready tasks

### Phase 7 — Task Graph (DAG)

* Workflow graph
* Dependency graph execution
* Parallel workflow scheduling

### Phase 8 — Event Bus

* Publish/Subscribe architecture
* Distributed event handling

### Phase 9 — LLM Planning Layer

* Dynamic task decomposition
* Dependency inference
* Agent selection

### Phase 10 — Autonomous Orchestration

* Self-organizing workflows
* Dynamic planning
* Adaptive execution

---

## Status

DAAOS is currently an active research and development project.

The current implementation focuses on establishing a robust orchestration runtime before introducing advanced planning, dependency resolution, and autonomous workflow generation.

---

## Inspiration

DAAOS draws ideas from:

* Multi-Agent Systems (MAS)
* Actor Model Architectures
* Event-Driven Systems
* Workflow Orchestration Engines
* Distributed Systems
* Autonomous Agent Frameworks

---

## License

MIT License
