# AgentNote: OODA-Driven Autonomous Agents for Iterative Notebook-Based Problem Solving

> **Talk is cheap, show me the notebook.**

[![](./docs/tch-badge.png)](https://zc.tencent.com/competition/competitionHackathon?code=cha004)

## 🧠 Core Philosophy

AgentNote implements OODA (Observe-Orient-Decide-Act) loop-driven autonomous agents for iterative problem solving in computational notebook environments. By orchestrating specialized AI agents through cognitive decision-making cycles, AgentNote enables autonomous exploration, analysis, and solution generation while automatically documenting the entire process in executable notebooks.

AgentNote is dedicated to creating a framework where AI agents can autonomously explore, experiment, and learn. Meanwhile, all thinking and execution processes are automatically documented into reproducible notebooks, effectively enhancing the readability, credibility, and reusability of agent decisions and executions.

## 🔬 Core Concepts

#### Circle
The highest-level execution unit representing a complete OODA iteration. Each circle contains four sequential phases and aims to make progress toward the mission goal through iterative refinement.

**Key Characteristics:**
- Contains 4 phases: Observe → Orient → Decide → Act
- Evaluates overall progress after each iteration
- Supports multiple circles for complex problem decomposition

#### Phase
The intermediate execution unit representing one of the four OODA stages within a circle. Each phase orchestrates specialized agents to accomplish specific cognitive tasks.

**Phase Types:**
- **Observe**: Environmental scanning and data collection
- **Orient**: Information synthesis and pattern recognition  
- **Decide**: Strategy formulation and decision making
- **Act**: Plan execution and solution implementation

#### Task
The fundamental execution unit within each phase, representing specific agent operations. Each phase contains three sequential tasks for comprehensive execution.

**Task Types:**
- **Commander Task**: Generates specific task descriptions for the phase
- **Agent Task**: Executes the specialized cognitive work using generated description
- **Reflection Task**: Evaluates task completion and provides feedback

#### Context
The shared memory system that maintains state across all execution levels based on persistent notebook cells, enabling continuity and learning across iterations.

**Context Components:**
- **Mission Context**: Overall goals and constraints
- **Circle Context**: Progress and insights from current iteration
- **Phase Context**: Stage-specific information and results
- **Task Context**: Execution details and error histories
- **Error Context**: Code execution error messages

## 🎯 Key Features

#### OODA-Driven Multi-Agent Architecture
- **Observe Agents**: Collect environmental data and self capabilities
- **Orient Agents**: Analyze and synthesize collected information
- **Decision Agents**: Formulate strategies and make informed decisions  
- **Action Agents**: Execute operations guided by decisions.
- **Commander Agents**: Simulate human experts and coordinate the entire OODA loop process

#### Autonomous Notebook Generation
- **Iterative Problem Solving**: Multiple OODA cycles for complex problem decomposition
- **Automatic Documentation**: Complete thought process captured in markdown and code cells
- **Executable Artifacts**: Generated notebooks are immediately executable and reproducible
- **Context Preservation**: Maintains state and context across iterative cycles

#### Advanced Capabilities
- **Intelligent Error Recovery**: Self-correcting mechanisms with contextual retry strategies
- **Online Reflection**: Continuous assessment of progress and goal achievement
- **Scalable Architecture**: Modular design supporting extensible agent capabilities

## ⚠️ Safety & Considerations
Important Security Notice: AgentNote executes AI-generated code in your local environment. Please exercise caution:

🔒 Code Execution: Generated code runs with your user permissions  
🔍 Code Review: Always review generated code before execution in production  
🛡️ Environment Isolation: Recommended to use virtual environments or containers  

## 📖 Citation
Our paper is coming Soon and we're working hard to bring you the full details!


## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

Start your journey in autonomous problem solving with AgentNote! 🚀

Where intelligent agents collaborate to transform complex problems into executable solutions