"""FastAPI Backend for Skyrchitect AI Agent"""

import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.models.schemas import (
    ArchitectureRequirement,
    ComponentOptimizationRequest,
    DiagramAnalysisRequest,
    ArchitectureRecommendation,
    OptimizationSuggestion,
    AgentResponse,
    HealthCheck
)
from backend.agents.architecture_agent import get_architecture_agent, ArchitectureAgent
from backend.agents.image_analysis_agent import get_image_analysis_agent
from backend.utils.response_parser import (
    parse_claude_architecture_response,
    transform_to_ui_format
)
from backend.utils.image_processor import ImageProcessor
from backend.utils.pdf_converter import PDFConverter
from backend.utils.s3_storage import get_s3_storage
from fastapi import UploadFile, File

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting Skyrchitect AI Backend...")
    logger.info(f"   AWS Region: {os.getenv('AWS_DEFAULT_REGION', 'us-west-2')}")
    logger.info(f"   Bedrock Model: {os.getenv('BEDROCK_MODEL_ID', 'claude-3-5-sonnet')}")

    try:
        # Initialize agent
        agent = get_architecture_agent()
        logger.info("✅ Architecture Agent initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize agent: {e}")
        logger.warning("   Agent will be initialized on first request")

    yield

    # Shutdown
    logger.info("👋 Shutting down Skyrchitect AI Backend")


# Create FastAPI app
app = FastAPI(
    title="Skyrchitect AI Backend",
    description="AI-powered cloud architecture design and optimization API using AWS Bedrock and Strands Agents",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative port
        "http://localhost:5174",
        "*"  # Allow all for hackathon demo
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get agent
def get_agent() -> ArchitectureAgent:
    """Dependency to get architecture agent"""
    try:
        return get_architecture_agent()
    except Exception as e:
        logger.error(f"Failed to get agent: {e}")
        raise HTTPException(status_code=503, detail="AI Agent not available. Please enable Bedrock model access.")


# Health check endpoint
@app.get("/", response_model=HealthCheck)
async def root():
    """API root and health check"""
    try:
        agent = get_architecture_agent()
        agent_ready = True
        bedrock_connected = True
    except Exception:
        agent_ready = False
        bedrock_connected = False

    return HealthCheck(
        status="healthy" if agent_ready else "degraded",
        version="1.0.0",
        agent_ready=agent_ready,
        bedrock_connected=bedrock_connected,
        model_id=os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
    )


@app.get("/health")
async def health_check():
    """Simple health check"""
    return {"status": "ok", "service": "Skyrchitect AI Backend"}


# AI Agent Endpoints

@app.post("/api/architecture/generate", response_model=AgentResponse)
async def generate_architecture(
    req: ArchitectureRequirement,
    agent: ArchitectureAgent = Depends(get_agent)
):
    """
    Generate cloud architecture based on requirements using AI agent
    """
    try:
        logger.info(f"\n{'='*80}")
        logger.info(f"📝 ARCHITECTURE GENERATION REQUEST")
        logger.info(f"{'='*80}")
        logger.info(f"Title: {req.title}")
        logger.info(f"Provider: {req.provider.value}")
        logger.info(f"Optimization Goal: {req.optimization_goal.value}")

        # Format requirements for agent
        requirements_text = f"""
Title: {req.title}
Description: {req.description}
Cloud Provider: {req.provider.value}
Optimization Goal: {req.optimization_goal.value}
"""

        # Add requirements only if they exist and are not empty
        if req.requirements and len(req.requirements) > 0:
            requirements_text += f"""
Requirements:
{chr(10).join(f"- {r}" for r in req.requirements)}
"""

        if req.budget:
            requirements_text += f"\nBudget: ${req.budget}/month"

        if req.expected_users:
            requirements_text += f"\nExpected Users: {req.expected_users:,}"

        logger.info(f"\n📤 Sending to AI:\n{requirements_text}")

        # Get agent recommendation
        response = agent.generate_architecture(requirements_text)

        logger.info(f"\n📥 AI Response received (length: {len(str(response))} chars)")
        logger.info(f"✅ Architecture generated successfully")
        logger.info(f"{'='*80}\n")

        # Parse hybrid response (JSON + markdown)
        architecture_json, markdown_reasoning = parse_claude_architecture_response(str(response))

        if architecture_json:
            logger.info(f"📊 Parsed Architecture JSON:")
            logger.info(f"   - Services: {len(architecture_json.get('architecture', {}).get('services', []))}")
            logger.info(f"   - Connections: {len(architecture_json.get('architecture', {}).get('connections', []))}")
            logger.info(f"   - Total Cost: ${architecture_json.get('architecture', {}).get('total_cost', 0)}/mo")

            # Transform to UI format
            ui_architecture = transform_to_ui_format(architecture_json, req.provider.value)

            return AgentResponse(
                success=True,
                message="Architecture generated successfully",
                data=ui_architecture,
                reasoning=markdown_reasoning
            )
        else:
            # Fallback if JSON extraction fails - return raw response
            logger.warning("⚠️ Could not extract JSON from response, returning raw format")
            return AgentResponse(
                success=True,
                message="Architecture generated successfully",
                data={
                    "architecture": str(response),
                    "provider": req.provider.value,
                    "optimization_goal": req.optimization_goal.value
                },
                reasoning=str(response)
            )

    except Exception as e:
        logger.error(f"Error generating architecture: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/architecture/optimize", response_model=AgentResponse)
async def optimize_architecture(
    req: ComponentOptimizationRequest,
    agent: ArchitectureAgent = Depends(get_agent)
):
    """
    Optimize existing architecture for cost or performance
    """
    try:
        logger.info(f"Optimizing architecture (goal: {req.optimization_goal.value})")

        # Format current architecture
        arch_description = f"""
Provider: {req.provider.value}
Current Monthly Cost: ${req.current_cost}
Optimization Goal: {req.optimization_goal.value}

Current Components:
{chr(10).join(f"- {c}" for c in req.components)}
"""

        # Get optimization recommendations
        response = agent.optimize_architecture(
            arch_description,
            req.optimization_goal.value
        )

        logger.info("✅ Optimization completed")

        return AgentResponse(
            success=True,
            message="Optimization recommendations generated",
            data={
                "optimizations": str(response),
                "current_cost": req.current_cost,
                "goal": req.optimization_goal.value
            },
            reasoning=str(response)
        )

    except Exception as e:
        logger.error(f"Error optimizing architecture: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/architecture/validate", response_model=AgentResponse)
async def validate_architecture(
    req: DiagramAnalysisRequest,
    agent: ArchitectureAgent = Depends(get_agent)
):
    """
    Validate architecture design and provide best practice recommendations
    """
    try:
        logger.info("Validating architecture design")

        # Format architecture for validation
        arch_description = f"""
Provider: {req.provider.value}

Services:
{chr(10).join(f"- {node}" for node in req.nodes)}

Connections:
{chr(10).join(f"- {edge}" for edge in req.edges)}
"""

        if req.requirements:
            arch_description += f"\nRequirements: {req.requirements}"

        # Validate with agent
        response = agent.validate_design(arch_description)

        logger.info("✅ Validation completed")

        return AgentResponse(
            success=True,
            message="Architecture validated",
            data={"validation": str(response)},
            reasoning=str(response)
        )

    except Exception as e:
        logger.error(f"Error validating architecture: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cloud/compare/{service_name}", response_model=AgentResponse)
async def compare_cloud_services(
    service_name: str,
    agent: ArchitectureAgent = Depends(get_agent)
):
    """
    Compare a service across AWS, Azure, and GCP
    """
    try:
        logger.info(f"Comparing service: {service_name}")

        response = agent.compare_providers(service_name)

        return AgentResponse(
            success=True,
            message=f"Comparison for {service_name}",
            data={"comparison": str(response)},
            reasoning=str(response)
        )

    except Exception as e:
        logger.error(f"Error comparing services: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat", response_model=AgentResponse)
async def chat_with_agent(
    question: dict,
    agent: ArchitectureAgent = Depends(get_agent)
):
    """
    Ask the AI agent a question about cloud architecture
    """
    try:
        user_question = question.get("question", "")
        context = question.get("context", None)

        logger.info(f"Chat question: {user_question[:50]}...")

        response = agent.answer_question(user_question, context)

        return AgentResponse(
            success=True,
            message="Response from AI agent",
            data={"answer": str(response)},
            reasoning=str(response)
        )

    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/code/generate", response_model=AgentResponse)
async def generate_infrastructure_code(
    request: dict
):
    """
    Generate Infrastructure as Code (Terraform or CloudFormation) based on architecture
    """
    try:
        import boto3
        import json

        architecture = request.get("architecture")
        code_type = request.get("code_type", "terraform")  # "terraform" or "cloudformation"

        logger.info(f"\n{'='*80}")
        logger.info(f"💻 CODE GENERATION REQUEST")
        logger.info(f"{'='*80}")
        logger.info(f"Code Type: {code_type.upper()}")
        logger.info(f"Provider: {architecture.get('provider', 'aws')}")
        logger.info(f"Components: {len(architecture.get('components', []))}")

        # Create prompt for code generation
        components_desc = "\n".join([
            f"- {comp.get('name', 'Unknown')}: {comp.get('description', '')}"
            for comp in architecture.get('components', [])
        ])

        prompt = f"""Generate complete, production-ready {code_type.upper()} code for this cloud architecture:

Provider: {architecture.get('provider', 'aws')}
Architecture: {architecture.get('name', 'Cloud Architecture')}

Components:
{components_desc}

Requirements:
- Include all necessary resources
- Add proper security configurations
- Include networking setup (VPC, subnets, security groups)
- Add resource tags for organization
- Include output variables for important endpoints
- Follow best practices for {architecture.get('provider', 'aws')}
- Keep the code concise and well-commented

Return ONLY the {code_type} code, no additional explanation."""

        # Use direct Bedrock API call to avoid conversation history buildup
        bedrock = boto3.client('bedrock-runtime', region_name=os.getenv('AWS_DEFAULT_REGION', 'us-west-2'))

        model_id = os.getenv('BEDROCK_MODEL_ID', 'us.anthropic.claude-sonnet-4-20250514-v1:0')

        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,  # Limit response length
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )

        response_body = json.loads(response['body'].read())
        code_response = response_body['content'][0]['text']

        logger.info(f"✅ Code generated successfully (length: {len(code_response)} chars)")
        logger.info(f"{'='*80}\n")

        return AgentResponse(
            success=True,
            message=f"{code_type.capitalize()} code generated successfully",
            data={
                "code": str(code_response),
                "code_type": code_type,
                "provider": architecture.get('provider', 'aws')
            },
            reasoning=str(code_response)
        )

    except Exception as e:
        logger.error(f"❌ Error generating code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/architecture/analyze-image", response_model=AgentResponse)
async def analyze_architecture_image(
    file: UploadFile = File(...)
):
    """
    Analyze uploaded architecture diagram image/PDF using AI vision
    """
    try:
        logger.info(f"📤 Received file: {file.filename}, type: {file.content_type}")

        # Read file content
        file_content = await file.read()
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''

        # Determine file type and process
        is_pdf = file_extension == 'pdf' or file.content_type == 'application/pdf'

        if is_pdf:
            # Validate and convert PDF
            is_valid, error_msg = PDFConverter.validate_pdf(file_content, file.filename)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)

            # Convert PDF to image
            image_bytes, pdf_error = PDFConverter.pdf_to_image(file_content)
            if pdf_error:
                raise HTTPException(status_code=400, detail=f"PDF conversion failed: {pdf_error}")

            content_type = 'image/png'
            processed_content = image_bytes

        else:
            # Validate image
            is_valid, error_msg = ImageProcessor.validate_image(file_content, file.filename)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)

            # Process image
            processed_bytes, img_error = ImageProcessor.process_image(file_content)
            if img_error:
                raise HTTPException(status_code=400, detail=f"Image processing failed: {img_error}")

            content_type = 'image/png'
            processed_content = processed_bytes

        # Backup to S3
        s3_storage = get_s3_storage()
        s3_url = s3_storage.upload_diagram(
            processed_content,
            file.filename,
            content_type=content_type,
            metadata={
                'original_type': file.content_type,
                'is_pdf': str(is_pdf)
            }
        )

        logger.info(f"✅ File backed up to S3: {s3_url}")

        # Encode image for AI analysis
        image_base64 = ImageProcessor.encode_image_base64(processed_content)

        # Analyze with AI
        analysis_agent = get_image_analysis_agent()
        analysis_result = analysis_agent.analyze_architecture_diagram(
            image_base64,
            image_format='png'
        )

        # Add S3 backup URL to response
        analysis_result['s3_backup_url'] = s3_url
        analysis_result['original_filename'] = file.filename

        # Transform detected components to UI format
        components = []
        for idx, comp in enumerate(analysis_result.get('detected_components', [])):
            components.append({
                'id': f"{comp['type']}-{idx+1}",
                'name': comp['service_name'],
                'category': comp.get('category', 'compute'),
                'type': comp['type'],
                'cost': round(analysis_result['estimated_monthly_cost'] / max(len(analysis_result['detected_components']), 1), 2),
                'description': f"{comp.get('description', '')} (Confidence: {comp['confidence']}%)",
                'confidence': comp['confidence']
            })

        # Create UI-compatible architecture
        ui_architecture = {
            'id': f"analyzed-{file.filename.split('.')[0]}",
            'name': f"Analyzed: {file.filename}",
            'provider': analysis_result.get('provider', 'aws'),
            'components': components,
            'optimization_goal': 'balanced',
            'estimated_cost': analysis_result.get('estimated_monthly_cost', 0),
            'complexity': analysis_result.get('complexity', 'medium'),
            's3_backup_url': s3_url,
            'diagram': {
                'nodes': [],  # Will be generated by frontend
                'edges': []
            }
        }

        logger.info(f"✅ Image analysis completed: {analysis_result.get('provider', 'unknown').upper()}, {len(components)} components")

        return AgentResponse(
            success=True,
            message="Architecture diagram analyzed successfully",
            data={
                'architecture': ui_architecture,
                'analysis_result': analysis_result,
                'detected_components': analysis_result.get('detected_components', [])
            },
            reasoning=analysis_result.get('architecture_pattern', 'Architecture analyzed from uploaded diagram')
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/deploy", response_model=AgentResponse)
async def deploy_architecture(
    request: dict,
    agent: ArchitectureAgent = Depends(get_agent)
):
    """
    Deploy architecture to cloud provider (simulation for hackathon)
    """
    try:
        architecture = request.get("architecture")
        config = request.get("config", {})

        provider = config.get("provider", architecture.get("provider", "aws"))
        region = config.get("region", "us-west-2")
        stack_name = config.get("stack_name", "skyrchitect-stack")

        logger.info(f"Deploying to {provider} in {region}...")

        # For hackathon: simulate deployment with AI-generated deployment plan
        deployment_prompt = f"""
Create a detailed deployment plan for the following architecture:

Provider: {provider}
Region: {region}
Stack Name: {stack_name}
Architecture: {architecture.get('name', 'Cloud Architecture')}

Components: {len(architecture.get('components', []))} resources

Generate a step-by-step deployment plan including:
1. Pre-deployment checks
2. Resource creation order
3. Configuration steps
4. Post-deployment validation
5. Estimated deployment time

Format as deployment logs with timestamps.
"""

        deployment_plan = agent.answer_question(deployment_prompt)

        # Simulate deployment logs
        logs = [
            f"[INFO] Initializing deployment to {provider}...",
            f"[INFO] Region: {region}",
            f"[INFO] Stack: {stack_name}",
            "[INFO] Validating architecture configuration...",
            "[SUCCESS] Configuration validated",
            "[INFO] Creating VPC and networking resources...",
            "[SUCCESS] Network infrastructure created",
            "[INFO] Deploying compute resources...",
            "[SUCCESS] Compute resources deployed",
            "[INFO] Configuring storage services...",
            "[SUCCESS] Storage configured",
            "[INFO] Setting up databases...",
            "[SUCCESS] Database instances created",
            "[INFO] Finalizing deployment...",
            "[SUCCESS] Deployment completed successfully!",
            f"[INFO] Access URL: https://{provider}-app-{stack_name}.example.com"
        ]

        return AgentResponse(
            success=True,
            message="Deployment completed successfully",
            data={
                "status": "success",
                "deployment_logs": logs,
                "deployment_plan": str(deployment_plan),
                "endpoint": f"https://{provider}-app-{stack_name}.example.com",
                "provider": provider,
                "region": region
            },
            reasoning=str(deployment_plan)
        )

    except Exception as e:
        logger.error(f"Error deploying architecture: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Run with: uvicorn backend.api.main:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
