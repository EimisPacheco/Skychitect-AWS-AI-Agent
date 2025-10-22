# Skyrchitect AI - AWS Lightsail Deployment Guide

AWS Lightsail is a **simpler, cheaper** alternative to ECS for deploying Skyrchitect AI. Perfect for the hackathon!

## Why Lightsail?

✅ **Simpler**: No complex VPC, ALB, or ECS configuration
✅ **Cheaper**: Starting at $10/month (vs $53/month with ECS)
✅ **Faster**: Deploy in 10 minutes instead of hours
✅ **Container Support**: Native Docker container hosting
✅ **HTTPS Included**: Free SSL certificates
✅ **Static IP**: Fixed public IP address

## Architecture

```
┌─────────────────────────────────────┐
│      AWS Lightsail Deployment       │
├─────────────────────────────────────┤
│                                     │
│  Container Service                  │
│  ├── Backend (FastAPI + Docker)     │
│  ├── Public HTTPS endpoint          │
│  ├── Auto-scaling (1-4 instances)   │
│  └── 1GB RAM, 0.5 vCPU             │
│                                     │
│  Static Hosting (Frontend)          │
│  ├── React/Vite build               │
│  ├── CloudFront CDN                 │
│  └── Custom domain support          │
│                                     │
│  Storage (S3 - separate)            │
│  └── Architecture diagrams          │
│                                     │
└─────────────────────────────────────┘
```

## Prerequisites

1. **AWS Account** with Bedrock access (Claude Sonnet 4 enabled)
2. **AWS CLI** installed and configured
3. **Docker** installed
4. **Lightsail CLI Plugin** (optional, for automation)

## Deployment Methods

### Option 1: AWS Console (Recommended for Beginners)

This is the easiest method - no CLI needed!

#### Step 1: Deploy Backend Container

1. **Go to AWS Lightsail Console**
   - Navigate to: https://lightsail.aws.amazon.com/
   - Click "Containers" in the left menu

2. **Create Container Service**
   - Click "Create container service"
   - Choose deployment location: `us-west-2` (or your preferred region)
   - Select capacity: **Micro** ($10/month) - 512 MB RAM, 0.25 vCPU
     - Or **Small** ($20/month) - 1 GB RAM, 0.5 vCPU (recommended)
   - Service name: `skyrchitect-backend`

3. **Set Up Container**
   - Click "Set up your first deployment"
   - Choose "Specify a custom deployment"

   **Container details:**
   ```
   Container name: backend
   Image: public.ecr.aws/docker/library/python:3.11-slim
   ```

   **For now, use a placeholder - we'll update with our image later**

4. **Configure Environment Variables**

   Add these environment variables:
   ```
   AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
   AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
   AWS_DEFAULT_REGION=us-west-2
   BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
   S3_BUCKET_NAME=skyrchitect-diagrams
   ```

5. **Configure Public Endpoint**
   - Enable "Public endpoint"
   - Health check path: `/health`
   - Container port: `8000`

6. **Create Service**
   - Click "Create container service"
   - Wait 5-10 minutes for deployment

#### Step 2: Build and Push Your Docker Image

Now we need to push our actual application image:

```bash
# Navigate to project directory
cd /path/to/project

# Build Docker image
docker build -t skyrchitect-backend .

# Push to Lightsail
aws lightsail push-container-image \
  --service-name skyrchitect-backend \
  --label backend-v1 \
  --image skyrchitect-backend:latest \
  --region us-west-2
```

This command will:
- Upload your image to Lightsail's private registry
- Return an image reference like: `:skyrchitect-backend.backend-v1.1`

#### Step 3: Update Deployment with Your Image

1. Go back to Lightsail Console → Your container service
2. Click "Deployments" tab
3. Click "Modify your deployment"
4. Update the image reference to the one returned from push command
5. Click "Save and deploy"

#### Step 4: Get Your Backend URL

1. Go to container service → "Public domain" tab
2. Copy the URL (looks like: `https://skyrchitect-backend.xxx.us-west-2.cs.amazonlightsail.com`)
3. Test it: `curl https://your-url/health`

#### Step 5: Deploy Frontend

**Option A: Lightsail Static Website (Simplest)**

1. In Lightsail Console, go to "Networking" → "Create distribution"
2. Choose "Origin": Create a new bucket
3. Bucket name: `skyrchitect-frontend`
4. Upload your frontend build:

```bash
# Build frontend with backend URL
export VITE_API_URL=https://your-lightsail-backend-url.cs.amazonlightsail.com
npm run build

# Create a zip of the dist folder
cd dist
zip -r ../frontend.zip .
cd ..
```

5. Upload `frontend.zip` to Lightsail bucket
6. Enable "Website hosting"
7. Get your CDN URL from the distribution

**Option B: S3 + CloudFront (More features)**

```bash
# Create S3 bucket
aws s3 mb s3://skyrchitect-frontend-prod

# Upload frontend
aws s3 sync dist/ s3://skyrchitect-frontend-prod --acl public-read

# Enable static website hosting
aws s3 website s3://skyrchitect-frontend-prod --index-document index.html
```

### Option 2: Lightsail CLI (Advanced/Automated)

For those comfortable with CLI, here's the complete automated deployment:

#### Deploy Backend

```bash
# Set variables
SERVICE_NAME="skyrchitect-backend"
REGION="us-west-2"
POWER="small"  # micro, small, medium, large, xlarge

# Create container service
aws lightsail create-container-service \
  --service-name $SERVICE_NAME \
  --power $POWER \
  --scale 1 \
  --region $REGION

# Build and push Docker image
docker build -t skyrchitect-backend .

aws lightsail push-container-image \
  --service-name $SERVICE_NAME \
  --label backend-v1 \
  --image skyrchitect-backend:latest \
  --region $REGION

# The above command outputs an image reference, save it
IMAGE_REF=":$SERVICE_NAME.backend-v1.1"  # Replace with actual output

# Create deployment configuration
cat > containers.json << EOF
{
  "backend": {
    "image": "$IMAGE_REF",
    "environment": {
      "AWS_ACCESS_KEY_ID": "YOUR_ACCESS_KEY",
      "AWS_SECRET_ACCESS_KEY": "YOUR_SECRET_KEY",
      "AWS_DEFAULT_REGION": "$REGION",
      "BEDROCK_MODEL_ID": "us.anthropic.claude-sonnet-4-20250514-v1:0"
    },
    "ports": {
      "8000": "HTTP"
    }
  }
}
EOF

cat > public-endpoint.json << EOF
{
  "containerName": "backend",
  "containerPort": 8000,
  "healthCheck": {
    "path": "/health",
    "intervalSeconds": 30
  }
}
EOF

# Deploy
aws lightsail create-container-service-deployment \
  --service-name $SERVICE_NAME \
  --containers file://containers.json \
  --public-endpoint file://public-endpoint.json \
  --region $REGION

# Get service URL
aws lightsail get-container-services \
  --service-name $SERVICE_NAME \
  --region $REGION \
  --query 'containerServices[0].url' \
  --output text
```

#### Deploy Frontend

```bash
# Build frontend
BACKEND_URL=$(aws lightsail get-container-services --service-name $SERVICE_NAME --region $REGION --query 'containerServices[0].url' --output text)
export VITE_API_URL=$BACKEND_URL
npm run build

# Create Lightsail bucket
aws lightsail create-bucket \
  --bucket-name skyrchitect-frontend \
  --bundle-id small_1_0 \
  --region $REGION

# Upload files
cd dist
for file in $(find . -type f); do
  aws lightsail put-instance-public-ports \
    --bucket-name skyrchitect-frontend \
    --key "${file#./}" \
    --body "$file"
done
cd ..

# Create CDN distribution
aws lightsail create-distribution \
  --distribution-name skyrchitect-cdn \
  --origin-name skyrchitect-frontend \
  --default-cache-behavior "behavior=cache" \
  --cache-behaviors "path=/,behavior=cache" \
  --bundle-id small_1_0 \
  --region $REGION
```

## Cost Comparison

### Lightsail Pricing (Monthly)

| Plan | CPU | RAM | Bandwidth | Price |
|------|-----|-----|-----------|-------|
| Micro | 0.25 vCPU | 512 MB | 500 GB | $10 |
| Small | 0.5 vCPU | 1 GB | 1 TB | $20 |
| Medium | 1 vCPU | 2 GB | 2 TB | $40 |
| Large | 2 vCPU | 4 GB | 3 TB | $80 |

**Recommended for Skyrchitect**: **Small** ($20/month)

### Complete Hackathon Cost (~$30/month)
- Container Service (Small): $20
- Static Hosting: $5
- S3 Storage: $1-2
- Bedrock API: Pay-per-use

**vs. ECS Option: $53-60/month**

## Scaling Configuration

Lightsail can auto-scale your containers:

```bash
# Set auto-scaling (1-4 instances)
aws lightsail update-container-service \
  --service-name skyrchitect-backend \
  --scale 2 \
  --region us-west-2
```

Or in Console:
1. Go to container service
2. Click "Change scale"
3. Set desired number (1-20)

## Monitoring and Logs

### View Logs

**Console:**
1. Go to Lightsail → Container services
2. Click your service
3. Click "Logs" tab
4. Select container and time range

**CLI:**
```bash
# Stream logs
aws lightsail get-container-log \
  --service-name skyrchitect-backend \
  --container-name backend \
  --region us-west-2 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ)
```

### Metrics

Lightsail provides built-in metrics:
- CPU utilization
- Memory utilization
- Request count
- Response time

Access in Console → Container service → Metrics tab

## Custom Domain (Optional)

1. **Register/Use Existing Domain**
2. **Create Lightsail Distribution** (if not already)
3. **Add Custom Domain**:
   ```bash
   aws lightsail attach-certificate-to-distribution \
     --distribution-name skyrchitect-cdn \
     --certificate-name your-cert
   ```
4. **Update DNS** - Point your domain to Lightsail distribution

## Updating Your Application

### Update Backend

```bash
# Build new version
docker build -t skyrchitect-backend .

# Push new version
aws lightsail push-container-image \
  --service-name skyrchitect-backend \
  --label backend-v2 \
  --image skyrchitect-backend:latest

# Update deployment (get new image reference from push output)
# Then use Console to modify deployment or use CLI:
aws lightsail create-container-service-deployment \
  --service-name skyrchitect-backend \
  --containers file://containers.json \
  --public-endpoint file://public-endpoint.json
```

### Update Frontend

```bash
# Rebuild
npm run build

# Upload to S3 or Lightsail bucket
aws s3 sync dist/ s3://skyrchitect-frontend-prod --delete

# Invalidate CloudFront cache if using S3+CloudFront
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

## Troubleshooting

### Container Won't Start

1. **Check logs**:
   ```bash
   aws lightsail get-container-log \
     --service-name skyrchitect-backend \
     --container-name backend
   ```

2. **Common issues**:
   - Missing environment variables
   - Bedrock access not enabled
   - Port mismatch (must be 8000)
   - Health check failing

### Bedrock Access Denied

1. Go to AWS Console → Bedrock → Model Access
2. Enable Claude Sonnet 4
3. Restart Lightsail container:
   ```bash
   aws lightsail update-container-service \
     --service-name skyrchitect-backend \
     --is-disabled false
   ```

### High Memory Usage

Upgrade to larger instance:
```bash
aws lightsail update-container-service \
  --service-name skyrchitect-backend \
  --power medium
```

## Cleanup

To delete everything and stop charges:

```bash
# Delete container service
aws lightsail delete-container-service \
  --service-name skyrchitect-backend

# Delete bucket
aws lightsail delete-bucket \
  --bucket-name skyrchitect-frontend

# Delete distribution
aws lightsail delete-distribution \
  --distribution-name skyrchitect-cdn

# Delete S3 bucket (if used)
aws s3 rb s3://skyrchitect-frontend-prod --force
```

## Deployment Checklist

- [ ] AWS Bedrock access enabled for Claude Sonnet 4
- [ ] Docker installed and tested locally
- [ ] AWS CLI configured with credentials
- [ ] Backend Docker image builds successfully
- [ ] Environment variables configured
- [ ] Container service created in Lightsail
- [ ] Backend deployed and health check passing
- [ ] Backend URL accessible
- [ ] Frontend built with correct API URL
- [ ] Frontend deployed to Lightsail or S3
- [ ] CORS configured correctly
- [ ] Application tested end-to-end
- [ ] Monitoring/logs verified
- [ ] URLs documented for submission

## Production Recommendations

For production use beyond the hackathon:

1. **Use Secrets Manager** for API keys instead of environment variables
2. **Enable HTTPS** with custom domain and SSL certificate
3. **Set up CloudWatch alarms** for errors and high resource usage
4. **Enable automatic backups** of S3 diagrams bucket
5. **Configure auto-scaling** based on CPU/memory metrics
6. **Add WAF** for security if handling sensitive data
7. **Use CloudFront** with Lightsail for better global performance

## Why Lightsail for This Hackathon?

✅ **Fast deployment**: 10 minutes vs hours with ECS
✅ **Lower cost**: $20-30/month vs $53-60/month
✅ **Simpler management**: No VPC, ALB, or ECS complexity
✅ **Same AWS services**: Full Bedrock, S3 access
✅ **Easy scaling**: Just adjust scale number
✅ **Built-in monitoring**: Metrics and logs included
✅ **HTTPS included**: Free SSL certificates
✅ **Perfect for demos**: Reliable, fast, professional URLs

## Example: Complete 5-Minute Deployment

```bash
#!/bin/bash
# Quick Lightsail Deployment Script

SERVICE_NAME="skyrchitect-backend"
REGION="us-west-2"

echo "🚀 Deploying Skyrchitect to AWS Lightsail..."

# 1. Build Docker image
echo "📦 Building Docker image..."
docker build -t skyrchitect-backend .

# 2. Create Lightsail container service (if not exists)
echo "🏗️ Creating Lightsail service..."
aws lightsail create-container-service \
  --service-name $SERVICE_NAME \
  --power small \
  --scale 1 \
  --region $REGION 2>/dev/null || echo "Service already exists"

# 3. Push Docker image
echo "📤 Pushing Docker image..."
aws lightsail push-container-image \
  --service-name $SERVICE_NAME \
  --label backend-v1 \
  --image skyrchitect-backend:latest \
  --region $REGION

# 4. Get backend URL
echo "🌐 Waiting for deployment..."
sleep 60

BACKEND_URL=$(aws lightsail get-container-services \
  --service-name $SERVICE_NAME \
  --region $REGION \
  --query 'containerServices[0].url' \
  --output text)

# 5. Build frontend
echo "🎨 Building frontend..."
export VITE_API_URL=$BACKEND_URL
npm run build

# 6. Upload to S3
echo "📤 Uploading frontend..."
aws s3 sync dist/ s3://skyrchitect-frontend-prod --acl public-read

echo "✅ Deployment complete!"
echo "Backend: $BACKEND_URL"
echo "Frontend: http://skyrchitect-frontend-prod.s3-website-$REGION.amazonaws.com"
```

Save as `deploy-lightsail.sh`, make executable, and run!

---

**Lightsail is the perfect choice for hackathon deployment** - simple, cheap, and professional! 🚀
