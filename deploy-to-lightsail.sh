#!/bin/bash

# Skyrchitect AI - Automated AWS Lightsail Deployment Script
# This script deploys both backend and frontend to AWS Lightsail

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - ALWAYS USE US-EAST-1 FOR BEDROCK
AWS_REGION="us-east-1"
CONTAINER_SERVICE_NAME="skyrchitect-backend"
CONTAINER_NAME="skyrchitect-app"
FRONTEND_BUCKET_NAME="skyrchitect-frontend-${AWS_REGION}"
POWER="nano"  # nano, micro, small, medium, large, xlarge
SCALE="1"     # Number of container instances

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Skyrchitect AI - Lightsail Deployment            ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Check prerequisites
echo -e "${YELLOW}[1/8] Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed or not in PATH${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon is not running. Please start Docker Desktop.${NC}"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed or not in PATH${NC}"
    exit 1
fi

# Verify AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials are not configured${NC}"
    exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ Prerequisites verified${NC}"
echo -e "   AWS Account: ${AWS_ACCOUNT_ID}"
echo -e "   AWS Region: ${AWS_REGION}"
echo ""

# Step 2: Build Docker image
echo -e "${YELLOW}[2/8] Building Docker image...${NC}"
docker build -t skyrchitect-backend:latest -f Dockerfile .
echo -e "${GREEN}✅ Docker image built successfully${NC}"
echo ""

# Step 3: Create Lightsail container service
echo -e "${YELLOW}[3/8] Creating/updating Lightsail container service...${NC}"

# Check if service already exists
if aws lightsail get-container-services --service-name "$CONTAINER_SERVICE_NAME" --region "$AWS_REGION" &> /dev/null; then
    echo -e "${BLUE}ℹ️  Container service '$CONTAINER_SERVICE_NAME' already exists${NC}"
else
    echo -e "${BLUE}Creating new container service '$CONTAINER_SERVICE_NAME'...${NC}"
    aws lightsail create-container-service \
        --service-name "$CONTAINER_SERVICE_NAME" \
        --power "$POWER" \
        --scale "$SCALE" \
        --region "$AWS_REGION"

    echo -e "${BLUE}⏳ Waiting for container service to become active (this may take 2-3 minutes)...${NC}"

    # Wait for service to be active
    for i in {1..60}; do
        SERVICE_STATE=$(aws lightsail get-container-services \
            --service-name "$CONTAINER_SERVICE_NAME" \
            --region "$AWS_REGION" \
            --query 'containerServices[0].state' \
            --output text 2>/dev/null || echo "PENDING")

        if [ "$SERVICE_STATE" = "ACTIVE" ] || [ "$SERVICE_STATE" = "RUNNING" ]; then
            break
        fi

        echo -e "${BLUE}   Status: $SERVICE_STATE (${i}/60)${NC}"
        sleep 5
    done
fi

echo -e "${GREEN}✅ Container service is ready${NC}"
echo ""

# Step 4: Push image to Lightsail
echo -e "${YELLOW}[4/8] Pushing Docker image to Lightsail...${NC}"

# Get push command and extract the commands
PUSH_INFO=$(aws lightsail push-container-image \
    --service-name "$CONTAINER_SERVICE_NAME" \
    --label skyrchitect-backend \
    --image skyrchitect-backend:latest \
    --region "$AWS_REGION" 2>&1)

# Extract the container image reference
CONTAINER_IMAGE=$(echo "$PUSH_INFO" | grep -o ':skyrchitect-backend\.[0-9]*' | head -1)

if [ -z "$CONTAINER_IMAGE" ]; then
    CONTAINER_IMAGE=":skyrchitect-backend.latest"
fi

echo -e "${GREEN}✅ Image pushed successfully${NC}"
echo -e "   Container image: ${CONTAINER_SERVICE_NAME}${CONTAINER_IMAGE}"
echo ""

# Step 5: Create deployment configuration
echo -e "${YELLOW}[5/8] Creating deployment configuration...${NC}"

# Get AWS credentials from environment
AWS_ACCESS_KEY="${AWS_ACCESS_KEY_ID}"
AWS_SECRET_KEY="${AWS_SECRET_ACCESS_KEY}"
AWS_REGION_ENV="${AWS_DEFAULT_REGION:-us-west-2}"
BEDROCK_MODEL="${BEDROCK_MODEL_ID:-us.anthropic.claude-sonnet-4-20250514-v1:0}"

cat > deployment-config.json <<EOF
{
  "serviceName": "$CONTAINER_SERVICE_NAME",
  "containers": {
    "$CONTAINER_NAME": {
      "image": "$CONTAINER_SERVICE_NAME$CONTAINER_IMAGE",
      "ports": {
        "8000": "HTTP"
      },
      "environment": {
        "AWS_ACCESS_KEY_ID": "$AWS_ACCESS_KEY",
        "AWS_SECRET_ACCESS_KEY": "$AWS_SECRET_KEY",
        "AWS_DEFAULT_REGION": "$AWS_REGION_ENV",
        "BEDROCK_MODEL_ID": "$BEDROCK_MODEL"
      }
    }
  },
  "publicEndpoint": {
    "containerName": "$CONTAINER_NAME",
    "containerPort": 8000,
    "healthCheck": {
      "path": "/health",
      "intervalSeconds": 30,
      "timeoutSeconds": 5,
      "healthyThreshold": 2,
      "unhealthyThreshold": 3
    }
  }
}
EOF

echo -e "${GREEN}✅ Deployment configuration created${NC}"
echo ""

# Step 6: Deploy container
echo -e "${YELLOW}[6/8] Deploying container to Lightsail...${NC}"

aws lightsail create-container-service-deployment \
    --region "$AWS_REGION" \
    --cli-input-json file://deployment-config.json

echo -e "${BLUE}⏳ Waiting for deployment to complete (this may take 3-5 minutes)...${NC}"

# Wait for deployment to complete
for i in {1..60}; do
    DEPLOYMENT_STATE=$(aws lightsail get-container-services \
        --service-name "$CONTAINER_SERVICE_NAME" \
        --region "$AWS_REGION" \
        --query 'containerServices[0].currentDeployment.state' \
        --output text 2>/dev/null || echo "PENDING")

    if [ "$DEPLOYMENT_STATE" = "ACTIVE" ]; then
        break
    fi

    echo -e "${BLUE}   Deployment status: $DEPLOYMENT_STATE (${i}/60)${NC}"
    sleep 5
done

# Get backend URL
BACKEND_URL=$(aws lightsail get-container-services \
    --service-name "$CONTAINER_SERVICE_NAME" \
    --region "$AWS_REGION" \
    --query 'containerServices[0].url' \
    --output text)

if [ "$DEPLOYMENT_STATE" = "ACTIVE" ]; then
    echo -e "${GREEN}✅ Backend deployed successfully!${NC}"
    echo -e "   Backend URL: https://${BACKEND_URL}"
else
    echo -e "${RED}❌ Deployment did not complete in expected time${NC}"
    echo -e "   Check status in AWS Lightsail console"
    exit 1
fi

echo ""

# Step 7: Build frontend with backend URL
echo -e "${YELLOW}[7/8] Building frontend with backend URL...${NC}"

# Export backend URL for frontend build
export VITE_API_URL="https://${BACKEND_URL}"

# Build frontend
npm run build

echo -e "${GREEN}✅ Frontend built successfully${NC}"
echo ""

# Step 8: Deploy frontend to S3
echo -e "${YELLOW}[8/8] Deploying frontend to S3...${NC}"

# Create S3 bucket if it doesn't exist
if ! aws s3 ls "s3://${FRONTEND_BUCKET_NAME}" 2>/dev/null; then
    echo -e "${BLUE}Creating S3 bucket...${NC}"
    aws s3 mb "s3://${FRONTEND_BUCKET_NAME}" --region "$AWS_REGION"

    # Enable static website hosting
    aws s3 website "s3://${FRONTEND_BUCKET_NAME}" \
        --index-document index.html \
        --error-document index.html

    # Set bucket policy for public access
    cat > bucket-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::${FRONTEND_BUCKET_NAME}/*"
    }
  ]
}
EOF

    # Disable block public access
    aws s3api put-public-access-block \
        --bucket "$FRONTEND_BUCKET_NAME" \
        --public-access-block-configuration \
        "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

    # Apply bucket policy
    aws s3api put-bucket-policy \
        --bucket "$FRONTEND_BUCKET_NAME" \
        --policy file://bucket-policy.json

    rm bucket-policy.json
fi

# Upload frontend files
aws s3 sync ./dist "s3://${FRONTEND_BUCKET_NAME}" --delete

FRONTEND_URL="http://${FRONTEND_BUCKET_NAME}.s3-website-${AWS_REGION}.amazonaws.com"

echo -e "${GREEN}✅ Frontend deployed successfully!${NC}"
echo -e "   Frontend URL: ${FRONTEND_URL}"
echo ""

# Cleanup
rm -f deployment-config.json

# Summary
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║            🎉 Deployment Complete! 🎉                     ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📋 Deployment Summary:${NC}"
echo -e "   Backend URL:  ${GREEN}https://${BACKEND_URL}${NC}"
echo -e "   Frontend URL: ${GREEN}${FRONTEND_URL}${NC}"
echo -e "   Region:       ${AWS_REGION}"
echo -e "   Container:    ${POWER} (${SCALE} instance)"
echo ""
echo -e "${BLUE}🔗 Quick Links:${NC}"
echo -e "   API Health:   ${GREEN}https://${BACKEND_URL}/health${NC}"
echo -e "   API Docs:     ${GREEN}https://${BACKEND_URL}/docs${NC}"
echo -e "   Application:  ${GREEN}${FRONTEND_URL}${NC}"
echo ""
echo -e "${YELLOW}💡 Next Steps:${NC}"
echo -e "   1. Test the backend: ${GREEN}curl https://${BACKEND_URL}/health${NC}"
echo -e "   2. Visit the frontend: ${GREEN}${FRONTEND_URL}${NC}"
echo -e "   3. Monitor logs in Lightsail console"
echo ""
echo -e "${BLUE}💰 Estimated Monthly Cost:${NC}"
echo -e "   Lightsail Container (nano): ~$7"
echo -e "   S3 + Data Transfer: ~$1-2"
echo -e "   Total: ~$8-9/month"
echo ""
echo -e "${YELLOW}🧹 To delete deployment later:${NC}"
echo -e "   aws lightsail delete-container-service --service-name $CONTAINER_SERVICE_NAME --region $AWS_REGION"
echo -e "   aws s3 rb s3://$FRONTEND_BUCKET_NAME --force"
echo ""
