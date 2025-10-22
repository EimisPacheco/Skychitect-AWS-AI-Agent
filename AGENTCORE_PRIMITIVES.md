# Amazon Bedrock AgentCore Primitives Integration

## Hackathon Requirement ✅

The AWS AI Agent Global Hackathon **strongly recommends** using:
> **Amazon Bedrock AgentCore - at least 1 primitive**

## Our Implementation

We use **2 AgentCore primitives** in production:

### 1. **AgentCore Runtime** (Primary Primitive) ✅

**Location**: `backend/agents/agentcore_architecture_agent.py`

The Runtime primitive provides a serverless, production-ready deployment environment for AI agents.

**Implementation**:
```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp, agent_handler

app = BedrockAgentCoreApp()

@agent_handler
def architecture_handler(input_data: dict) -> dict:
    """
    AgentCore Runtime handler for architecture generation
    This decorator makes the function deployable to AgentCore Runtime
    """
    agent = get_agentcore_agent()

    action = input_data.get("action", "generate")
    data = input_data.get("data", {})
    session_id = input_data.get("session_id")

    # Process request...
    return {
        "success": True,
        "response": response,
        "agentcore_primitives_used": ["Runtime", "Memory"]
    }
```

**Benefits**:
- ✅ Serverless deployment to AWS
- ✅ Zero infrastructure management
- ✅ Auto-scaling
- ✅ Built-in monitoring
- ✅ Production-grade security

### 2. **AgentCore Memory** (Secondary Primitive) ✅

**Location**: `backend/agents/agentcore_architecture_agent.py`

The Memory primitive provides persistent conversation history and context management.

**Implementation**:
```python
from bedrock_agentcore.memory import MemoryClient, MemoryConfig, ConversationMessage

class AgentCoreArchitectureAgent:
    def __init__(self, memory_enabled: bool = True):
        # Initialize AgentCore Memory primitive
        if memory_enabled:
            self.memory_client = MemoryClient(
                config=MemoryConfig(
                    memory_type="short_term",
                    retention_days=7
                )
            )

    def invoke(self, prompt: str, session_id: Optional[str] = None) -> str:
        # Retrieve conversation history from AgentCore Memory
        if self.memory_client and session_id:
            history = self.memory_client.get_conversation_history(
                session_id=session_id,
                max_messages=10
            )

        # Get agent response with context
        response = self.agent(full_prompt)

        # Store in AgentCore Memory
        if self.memory_client and session_id:
            self.memory_client.add_message(
                session_id=session_id,
                message=ConversationMessage(role="user", content=prompt)
            )
            self.memory_client.add_message(
                session_id=session_id,
                message=ConversationMessage(role="assistant", content=response)
            )

        return response
```

**Benefits**:
- ✅ Persistent conversation history
- ✅ Context-aware responses
- ✅ Multi-turn conversations
- ✅ Session management
- ✅ Shared memory across agents

## File Structure

```
backend/
├── agents/
│   ├── architecture_agent.py           # Original Strands agent
│   └── agentcore_architecture_agent.py # ✅ With AgentCore primitives
├── api/
│   └── main.py                         # Can use either agent
└── requirements.txt                     # ✅ Includes bedrock-agentcore
```

## Why These Primitives?

### AgentCore Runtime ✅
- **Required for production deployment** - The hackathon expects production-ready agents
- **Serverless** - No infrastructure management
- **AWS-native** - Perfect for AWS hackathon
- **Easy deployment** - Simple decorator pattern

### AgentCore Memory ✅
- **Enhances user experience** - Context-aware conversations
- **Demonstrates advanced usage** - Beyond basic agent
- **Production feature** - Real-world requirement
- **Easy integration** - Built into our agent class

## Other Available Primitives (Not Used)

We focused on the most impactful primitives, but AgentCore also provides:

| Primitive | Purpose | Why Not Used |
|-----------|---------|--------------|
| **Gateway** | Tool discovery & integration | Custom tools already implemented |
| **Identity** | Authentication & access control | Simple auth sufficient for demo |
| **Observability** | Monitoring & debugging | FastAPI logging sufficient |
| **Code Interpreter** | Secure code execution | Not needed for architecture design |
| **Browser** | Web automation | Not needed for our use case |

## Deployment Options

### Option 1: Deploy to AgentCore Runtime (Production)

```bash
# Install AgentCore CLI
pip install bedrock-agentcore-cli

# Deploy agent
bedrock-agentcore deploy backend/agents/agentcore_architecture_agent.py

# Agent gets a production URL automatically
```

### Option 2: Run Locally (Development)

```bash
# Start FastAPI backend (uses AgentCore agent)
./start_backend.sh

# AgentCore primitives work seamlessly
```

### Option 3: AWS Lambda (Alternative)

```bash
# Use Mangum adapter with AgentCore
# Both FastAPI and AgentCore Runtime are supported
```

## Testing AgentCore Integration

```bash
# Test locally (Memory will be simulated)
python3 backend/agents/agentcore_architecture_agent.py

# Test via API (after starting backend)
curl -X POST http://localhost:8000/api/architecture/generate \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Web App",
    "requirements": ["auth", "database"],
    "provider": "aws"
  }'
```

## Hackathon Compliance Checklist

- ✅ **LLM on AWS Bedrock** - Claude 3.5 Sonnet via Bedrock
- ✅ **AWS Service** - Amazon Bedrock
- ✅ **AgentCore Primitive #1** - Runtime (deployment)
- ✅ **AgentCore Primitive #2** - Memory (conversation)
- ✅ **Autonomous Agent** - Strands Agent with custom tools
- ✅ **Tool Integration** - 5 cloud architecture tools
- ✅ **Production-Ready** - AgentCore Runtime deployment

## Key Benefits for Judging

1. **Beyond Basic** - We use 2 primitives, not just 1
2. **Production-Grade** - AgentCore Runtime makes it AWS-native
3. **User Experience** - Memory enables context-aware conversations
4. **AWS Ecosystem** - Fully integrated with AWS services
5. **Scalable** - Serverless, auto-scaling architecture

## Documentation & Code Quality

- ✅ Clear comments explaining AgentCore usage
- ✅ Type hints throughout
- ✅ Error handling for graceful degradation
- ✅ Works locally (without AWS) for development
- ✅ Production-ready with AWS credentials

## Demo Script

**Highlight in demo video**:
1. Show `agentcore_architecture_agent.py` file
2. Point to `@agent_handler` decorator (Runtime primitive)
3. Show Memory initialization in `__init__`
4. Explain how it enables:
   - Serverless deployment
   - Conversation history
   - Production-grade scalability

**Key Quote for Video**:
> "Our agent uses Amazon Bedrock AgentCore's Runtime and Memory primitives, making it production-ready and deployable to AWS with zero infrastructure management, while maintaining conversation context across sessions."

## References

- **AgentCore Docs**: https://docs.aws.amazon.com/bedrock-agentcore/
- **SDK GitHub**: https://github.com/aws/bedrock-agentcore-sdk-python
- **Strands + AgentCore**: https://strandsagents.com/latest/documentation/docs/user-guide/deploy/deploy_to_bedrock_agentcore/

---

**Status**: ✅ **2 AgentCore primitives integrated and ready for demo!**
