"""
Image Analysis Agent for Skyrchitect AI
Uses AWS Bedrock Claude Sonnet 4 Vision to analyze architecture diagrams
"""

import os
import json
import boto3
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ImageAnalysisAgent:
    """AI Agent for analyzing cloud architecture diagrams using vision"""

    def __init__(self):
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
        )
        self.model_id = os.getenv(
            'BEDROCK_MODEL_ID',
            'anthropic.claude-3-5-sonnet-20241022-v2:0'
        )

    def analyze_architecture_diagram(
        self,
        image_base64: str,
        image_format: str = 'png'
    ) -> Dict:
        """
        Analyze cloud architecture diagram using Claude Sonnet 4 Vision

        Args:
            image_base64: Base64 encoded image
            image_format: Image format (png, jpeg, webp)

        Returns:
            Dictionary with analysis results
        """
        try:
            logger.info("🔍 Analyzing architecture diagram with Claude Sonnet 4 Vision...")

            # Prepare vision prompt
            analysis_prompt = self._create_analysis_prompt()

            # Prepare message for Claude Vision API
            message_content = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": f"image/{image_format}",
                        "data": image_base64
                    }
                },
                {
                    "type": "text",
                    "text": analysis_prompt
                }
            ]

            # Call Bedrock API with vision
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "temperature": 0.3,  # Lower temperature for more consistent analysis
                "messages": [
                    {
                        "role": "user",
                        "content": message_content
                    }
                ]
            }

            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )

            # Parse response
            response_body = json.loads(response['body'].read())
            analysis_text = response_body['content'][0]['text']

            logger.info("✅ Diagram analysis completed")
            logger.debug(f"Raw analysis: {analysis_text[:200]}...")

            # Parse the JSON response from Claude
            analysis_data = self._parse_analysis_response(analysis_text)

            return analysis_data

        except Exception as e:
            logger.error(f"❌ Error analyzing diagram: {e}")
            raise

    def _create_analysis_prompt(self) -> str:
        """Create detailed prompt for architecture analysis"""
        return """You are an expert cloud architecture analyst. Analyze this cloud architecture diagram and extract the following information:

1. **Cloud Provider**: Identify the cloud provider (AWS, Azure, or GCP) based on the service icons and naming conventions visible in the diagram.

2. **Components**: Identify all cloud services and components shown in the diagram. For each component, provide:
   - Component type (load_balancer, compute, database, storage, cache, cdn, networking, security, serverless, etc.)
   - Specific service name (e.g., "Application Load Balancer", "EC2", "RDS", "S3", etc.)
   - Confidence score (0-100%) indicating how certain you are about the identification

3. **Architecture Complexity**: Assess the overall complexity as:
   - "low" - Simple, few components (1-3)
   - "medium" - Moderate complexity (4-8 components)
   - "high" - Complex architecture (9+ components)

4. **Connections**: Identify the relationships and data flow between components

5. **Estimated Cost**: Provide a rough monthly cost estimate in USD based on typical usage

Return your analysis as a JSON object with this exact structure:

```json
{
  "provider": "aws" | "azure" | "gcp",
  "detected_components": [
    {
      "type": "component_type",
      "service_name": "Specific Service Name",
      "confidence": 95,
      "category": "network" | "compute" | "database" | "storage" | "cache" | "cdn" | "security" | "serverless",
      "description": "Brief description of what this component does"
    }
  ],
  "complexity": "low" | "medium" | "high",
  "estimated_monthly_cost": 245.50,
  "connections": [
    {
      "from": "component_index",
      "to": "component_index",
      "type": "http" | "tcp" | "data_flow" | "api_call"
    }
  ],
  "architecture_pattern": "Brief description of the overall architecture pattern",
  "recommendations": [
    "Optional: List any recommendations for improvement"
  ]
}
```

**Important Guidelines:**
- Only include components you can clearly identify with >70% confidence
- Use standard cloud service names (e.g., "Application Load Balancer" not "ALB")
- Be conservative with cost estimates
- Identify the provider based on visual clues like icons, service names, and diagram style
- If the diagram is unclear or unreadable, set low confidence scores

**Component Type Mapping:**
- Load Balancers → type: "load_balancer", category: "network"
- VMs/Instances → type: "virtual_machine", category: "compute"
- Containers/ECS/AKS → type: "container", category: "compute"
- Lambda/Functions → type: "function", category: "serverless"
- Databases → type: "database", category: "database"
- Object Storage → type: "object_storage", category: "storage"
- Cache (Redis/Memcached) → type: "cache", category: "cache"
- CDN → type: "cdn", category: "cdn"
- VPC/VNet → type: "vpc", category: "network"
- API Gateway → type: "api_gateway", category: "serverless"

Return ONLY the JSON object, no additional text."""

    def _parse_analysis_response(self, response_text: str) -> Dict:
        """Parse Claude's analysis response into structured data"""
        try:
            # Try to extract JSON from response
            # Sometimes Claude wraps JSON in markdown code blocks
            if "```json" in response_text:
                # Extract JSON from markdown code block
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
            elif "```" in response_text:
                # Extract from generic code block
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
            else:
                # Assume the entire response is JSON
                json_str = response_text.strip()

            # Parse JSON
            data = json.loads(json_str)

            # Validate required fields
            required_fields = ['provider', 'detected_components', 'complexity', 'estimated_monthly_cost']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            logger.info(f"✓ Parsed analysis: {data['provider'].upper()}, {len(data['detected_components'])} components, ${data['estimated_monthly_cost']}/mo")

            return data

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text}")

            # Return a default structure with error
            return {
                "provider": "aws",
                "detected_components": [],
                "complexity": "medium",
                "estimated_monthly_cost": 0,
                "connections": [],
                "error": "Failed to parse AI response",
                "raw_response": response_text[:500]
            }


# Singleton instance
_image_analysis_agent = None

def get_image_analysis_agent() -> ImageAnalysisAgent:
    """Get or create ImageAnalysisAgent singleton"""
    global _image_analysis_agent
    if _image_analysis_agent is None:
        _image_analysis_agent = ImageAnalysisAgent()
    return _image_analysis_agent
