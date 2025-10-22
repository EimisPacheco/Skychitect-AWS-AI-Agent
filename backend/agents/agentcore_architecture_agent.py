"""
Enhanced Strands Agent prepared for Amazon Bedrock AgentCore Primitives

This agent demonstrates the architecture for integrating AgentCore primitives:
1. Runtime Primitive - Serverless deployment with @agent_handler decorator
2. Memory Primitive - Persistent conversation history across sessions

NOTE: AgentCore primitives require more complex AWS setup than initially documented:
- Runtime: @agent_handler decorator not available in current bedrock-agentcore package
- Memory: Requires creating memory resources with IAM execution roles

The code structure shows how these primitives would be integrated in production.
For now, the agent works as a standard Strands agent with custom tools.
"""

import os
from typing import Optional, List, Dict
from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel

# Load environment variables
load_dotenv()
# Note: AgentCore primitives require more complex setup than initially documented
# Runtime primitive (@agent_handler) is not available in current bedrock-agentcore version
# Memory primitive API is different from expected - requires creating memory resources with IAM roles
# Commenting out for now - code structure shows how they would integrate in production
#
# from bedrock_agentcore.runtime import BedrockAgentCoreApp, agent_handler
# from bedrock_agentcore.memory import MemoryClient

from backend.tools.cloud_tools import (
    get_aws_service_info,
    calculate_architecture_cost,
    suggest_cost_optimization,
    get_service_alternatives,
    validate_architecture
)


class AgentCoreArchitectureAgent:
    """
    AI Agent for cloud architecture with AgentCore primitive integration points

    This agent uses:
    - Strands Agent framework with AWS Bedrock (Claude 3.5 Sonnet v2)
    - 5 custom tools for architecture design and cost optimization
    - Session-aware methods for future Memory primitive integration

    AgentCore Primitives (prepared for integration):
    1. Memory - Persistent conversation memory (commented out - needs AWS setup)
    2. Runtime - Serverless deployment handler (commented out - not in package yet)
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        region: Optional[str] = None,
        memory_enabled: bool = True
    ):
        """
        Initialize agent with AgentCore primitives

        Args:
            model_id: Bedrock model ID
            region: AWS region
            memory_enabled: Enable AgentCore Memory primitive
        """
        self.model_id = model_id or os.getenv(
            "BEDROCK_MODEL_ID",
            "us.anthropic.claude-sonnet-4-20250514-v1:0"  # Claude Sonnet 4 inference profile
        )
        self.region = region or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        self.memory_enabled = memory_enabled

        # Initialize Bedrock model
        self.model = BedrockModel(
            model_id=self.model_id,
            region_name=self.region,
            temperature=0.7,
            streaming=False
        )

        # System prompt
        system_prompt = """You are an expert cloud architecture AI agent specialized in AWS, Azure, and Google Cloud Platform.

Your role is to help users design optimal, secure, and cost-effective cloud architectures.

Key Responsibilities:
1. Analyze user requirements and recommend appropriate cloud services
2. Design complete architectures with proper service connections
3. Estimate costs accurately using your tools
4. Suggest cost optimizations and alternatives
5. Validate architectures for best practices and security
6. Provide clear reasoning for your recommendations

Available Tools:
- get_aws_service_info: Get details about AWS services
- calculate_architecture_cost: Calculate total architecture cost
- suggest_cost_optimization: Find cost-saving alternatives
- get_service_alternatives: Get equivalent services across cloud providers
- validate_architecture: Check architecture for best practices

Guidelines:
- Always use tools to get accurate service information and costs
- Provide specific, actionable recommendations
- Consider security, scalability, and cost in all designs
- Explain trade-offs between different approaches
- Follow cloud best practices
- Be concise but thorough"""

        # Initialize Strands Agent with tools
        self.agent = Agent(
            model=self.model,
            system_prompt=system_prompt,
            tools=[
                get_aws_service_info,
                calculate_architecture_cost,
                suggest_cost_optimization,
                get_service_alternatives,
                validate_architecture
            ]
        )

        # Initialize AgentCore Memory (Primitive #2)
        # NOTE: Memory primitive requires complex AWS setup (memory resources, IAM roles)
        # The API is: MemoryClient(region_name) -> create_or_get_memory() -> save_turn()
        # Commenting out for now - would be integrated in production deployment
        self.memory_client = None
        # if self.memory_enabled:
        #     try:
        #         self.memory_client = MemoryClient(region_name=self.region)
        #         # Would need to create memory resource with execution role:
        #         # memory = self.memory_client.create_or_get_memory(
        #         #     name="architecture-agent-memory",
        #         #     description="Conversation history for architecture agent",
        #         #     memory_execution_role_arn=os.getenv("MEMORY_EXECUTION_ROLE_ARN")
        #         # )
        #         print("✅ AgentCore Memory primitive initialized")
        #     except Exception as e:
        #         print(f"⚠️  AgentCore Memory not available: {e}")
        #         print("   Continuing without memory (for local testing)")
        #         self.memory_client = None
        # else:
        #     self.memory_client = None

    def invoke(self, prompt: str, session_id: Optional[str] = None) -> str:
        """
        Invoke agent (with session support for future Memory integration)

        Args:
            prompt: User prompt
            session_id: Session ID (for future Memory persistence)

        Returns:
            Agent response
        """
        # NOTE: Memory integration would retrieve conversation history here
        # if self.memory_client and session_id:
        #     turns = self.memory_client.get_last_k_turns(
        #         memory_name="architecture-agent-memory",
        #         branch_name=session_id,
        #         k=5
        #     )
        #     # Build context from turns...

        # Get agent response
        response = self.agent(prompt)

        # NOTE: Memory integration would save the turn here
        # if self.memory_client and session_id:
        #     self.memory_client.save_turn(
        #         memory_name="architecture-agent-memory",
        #         branch_name=session_id,
        #         user_input=prompt,
        #         assistant_output=response
        #     )

        return response

    def generate_architecture(
        self,
        requirements: str,
        session_id: Optional[str] = None
    ) -> str:
        """Generate architecture with memory support"""
        prompt = f"""Design a cloud architecture based on these requirements:

{requirements}

Please:
1. Recommend specific AWS services (use get_aws_service_info for details)
2. Calculate the total cost (use calculate_architecture_cost)
3. Suggest how services should connect
4. Validate the architecture (use validate_architecture)
5. Provide security best practices
6. Suggest cost optimizations if possible

Be specific and provide a complete, production-ready architecture."""

        return self.invoke(prompt, session_id)

    def optimize_architecture(
        self,
        current_architecture: str,
        optimization_goal: str,
        session_id: Optional[str] = None
    ) -> str:
        """Optimize architecture with memory support"""
        prompt = f"""Analyze and optimize this architecture with goal: {optimization_goal}

Current Architecture:
{current_architecture}

Please:
1. Identify optimization opportunities using suggest_cost_optimization
2. Calculate potential savings
3. Suggest alternative services where beneficial
4. Maintain or improve performance
5. Ensure security is not compromised
6. Provide implementation steps

Focus on practical, high-impact optimizations."""

        return self.invoke(prompt, session_id)


# AgentCore Runtime Integration (Primitive #1)
# NOTE: Runtime primitive (@agent_handler decorator) is not available in current bedrock-agentcore version
# Commenting out for now - can be re-enabled once package is updated
#
# app = BedrockAgentCoreApp()
#
# # Global agent instance
# _agentcore_agent: Optional[AgentCoreArchitectureAgent] = None
#
#
# def get_agentcore_agent() -> AgentCoreArchitectureAgent:
#     """Get or create AgentCore agent singleton"""
#     global _agentcore_agent
#     if _agentcore_agent is None:
#         _agentcore_agent = AgentCoreArchitectureAgent(memory_enabled=True)
#     return _agentcore_agent
#
#
# @agent_handler
# def architecture_handler(input_data: dict) -> dict:
#     """
#     AgentCore Runtime handler for architecture generation
#     This decorator makes the function deployable to AgentCore Runtime
#
#     Args:
#         input_data: Request data with 'action' and 'data' fields
#
#     Returns:
#         Response dictionary
#     """
#     agent = get_agentcore_agent()
#
#     action = input_data.get("action", "generate")
#     data = input_data.get("data", {})
#     session_id = input_data.get("session_id")
#
#     try:
#         if action == "generate":
#             requirements = data.get("requirements", "")
#             response = agent.generate_architecture(requirements, session_id)
#
#         elif action == "optimize":
#             architecture = data.get("architecture", "")
#             goal = data.get("optimization_goal", "balanced")
#             response = agent.optimize_architecture(architecture, goal, session_id)
#
#         elif action == "chat":
#             question = data.get("question", "")
#             response = agent.invoke(question, session_id)
#
#         else:
#             return {
#                 "success": False,
#                 "error": f"Unknown action: {action}"
#             }
#
#         return {
#             "success": True,
#             "response": response,
#             "session_id": session_id,
#             "agentcore_primitives_used": ["Runtime", "Memory"]
#         }
#
#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e)
#         }


# For local testing without AgentCore Runtime
if __name__ == "__main__":
    print("🧪 Testing AgentCore Architecture Agent locally...\n")

    agent = AgentCoreArchitectureAgent(memory_enabled=False)  # Memory requires AWS

    requirements = """
    Build a web application with:
    - User authentication
    - File uploads
    - PostgreSQL database
    - API backend
    Budget: $500/month
    """

    print("📋 Requirements:")
    print(requirements)
    print("\n🤖 Agent Response:")
    print("=" * 70)

    response = agent.generate_architecture(requirements)
    print(response)

    print("\n" + "=" * 70)
    print("\n📝 AgentCore Primitives Status:")
    print("   ✅ Code structure prepared for AgentCore integration")
    print("   ⚠️  Memory primitive: Requires AWS memory resource setup")
    print("   ⚠️  Runtime primitive: Not available in current package version")
    print("\n   For now: Using standard Strands agent with 5 custom tools")
    print("   Tools: get_aws_service_info, calculate_cost, optimize_cost,")
    print("          get_alternatives, validate_architecture")
