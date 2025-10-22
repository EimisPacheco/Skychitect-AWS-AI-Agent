"""Strands Agent for Cloud Architecture Recommendations"""

import os
from typing import Optional
from strands import Agent
from strands.models import BedrockModel
from backend.tools.cloud_tools import (
    get_aws_service_info,
    calculate_architecture_cost,
    suggest_cost_optimization,
    get_service_alternatives,
    validate_architecture
)


class ArchitectureAgent:
    """AI Agent for cloud architecture design and optimization"""

    def __init__(self, model_id: Optional[str] = None, region: Optional[str] = None):
        """
        Initialize the architecture agent with Bedrock model

        Args:
            model_id: Bedrock model ID (defaults to Claude 3.5 Sonnet)
            region: AWS region (defaults to us-west-2)
        """
        self.model_id = model_id or os.getenv(
            "BEDROCK_MODEL_ID",
            "us.anthropic.claude-sonnet-4-20250514-v1:0"  # Claude Sonnet 4 inference profile
        )
        self.region = region or os.getenv("AWS_DEFAULT_REGION", "us-east-1")

        # Initialize Bedrock model
        self.model = BedrockModel(
            model_id=self.model_id,
            region_name=self.region,
            temperature=0.7,
            streaming=False
        )

        # System prompt for architecture agent
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
- Follow cloud best practices (high availability, disaster recovery, monitoring)

CRITICAL OUTPUT FORMAT:
You MUST return your response in this EXACT JSON structure, followed by detailed markdown reasoning:

```json
{
  "architecture": {
    "title": "Project Title",
    "description": "Brief project description",
    "provider": "aws|azure|gcp",
    "total_cost": 229.00,
    "services": [
      {
        "id": "service-1",
        "name": "EC2 Instance",
        "type": "compute",
        "cost": 29.20,
        "description": "Primary application server",
        "icon": "server",
        "position": {"x": 300, "y": 200}
      }
    ],
    "connections": [
      {"from": "service-1", "to": "service-2", "type": "HTTP/HTTPS"}
    ],
    "alternatives": [
      {
        "service_id": "service-1",
        "alternative_name": "EC2 t3.small",
        "cost": 14.60,
        "savings": 14.60,
        "performance": 70,
        "description": "Smaller instance size"
      }
    ]
  }
}
```

IMPORTANT NODE POSITIONING RULES:
- Space nodes FAR APART to prevent visual clutter and make connections clearly visible
- Minimum horizontal spacing between nodes: 400 pixels
- Minimum vertical spacing between nodes: 300 pixels
- Arrange nodes in logical layers (e.g., frontend at top, backend in middle, data at bottom)
- Example positions for a 5-node architecture:
  * Node 1 (frontend): {"x": 100, "y": 100}
  * Node 2 (app server): {"x": 100, "y": 500}
  * Node 3 (database): {"x": 100, "y": 900}
  * Node 4 (storage): {"x": 600, "y": 500}
  * Node 5 (cache): {"x": 600, "y": 900}
- This generous spacing ensures connection lines are easily visible and the diagram remains readable

Then provide detailed markdown explanation with:
- Architecture overview
- Security best practices
- Cost breakdown
- Optimization recommendations
- Implementation steps"""

        # Create agent with tools
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

    def generate_architecture(self, requirements: str) -> str:
        """
        Generate architecture recommendation based on requirements

        Args:
            requirements: User's architecture requirements

        Returns:
            Agent's architecture recommendation
        """
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

        return self.agent(prompt)

    def optimize_architecture(self, current_architecture: str, optimization_goal: str) -> str:
        """
        Optimize an existing architecture

        Args:
            current_architecture: Description of current architecture
            optimization_goal: 'cost', 'performance', or 'balanced'

        Returns:
            Optimization recommendations
        """
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

        return self.agent(prompt)

    def validate_design(self, architecture_description: str) -> str:
        """
        Validate architecture design

        Args:
            architecture_description: Architecture to validate

        Returns:
            Validation results with recommendations
        """
        prompt = f"""Validate this cloud architecture design:

{architecture_description}

Use the validate_architecture tool and provide:
1. Validation results
2. Security concerns
3. Scalability issues
4. Best practice violations
5. Recommended improvements
6. Priority of each issue"""

        return self.agent(prompt)

    def compare_providers(self, service_name: str) -> str:
        """
        Compare a service across cloud providers

        Args:
            service_name: Service to compare

        Returns:
            Comparison across AWS, Azure, GCP
        """
        prompt = f"""Compare the service "{service_name}" across AWS, Azure, and Google Cloud.

Use get_service_alternatives tool and provide:
1. Equivalent services in each cloud
2. Key feature differences
3. Cost comparison (if available)
4. When to choose each provider
5. Migration considerations"""

        return self.agent(prompt)

    def answer_question(self, question: str, context: Optional[str] = None) -> str:
        """
        Answer general architecture questions

        Args:
            question: User's question
            context: Optional context about their architecture

        Returns:
            Agent's answer
        """
        if context:
            prompt = f"""Context: {context}

Question: {question}

Provide a clear, practical answer using tools if needed."""
        else:
            prompt = question

        return self.agent(prompt)


# Singleton instance
_agent_instance: Optional[ArchitectureAgent] = None


def get_architecture_agent() -> ArchitectureAgent:
    """Get or create the architecture agent singleton"""
    global _agent_instance

    if _agent_instance is None:
        _agent_instance = ArchitectureAgent()

    return _agent_instance
