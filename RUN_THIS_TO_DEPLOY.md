# 🚀 Deploy Skyrchitect AI to AWS - RUN THIS

## Step 1: Start Docker Desktop
1. Open **Docker Desktop** application from your Applications folder
2. Wait for it to show "Engine running" status (green icon in menu bar)

## Step 2: Open Terminal and Run

Copy and paste this entire command block into your terminal:

```bash
cd "/Users/eimis/Documents/HACKTHONS-2025/AMAZON HACKTHONS/AWS AI Agent Global Hackathon/project" && \
export AWS_ACCESS_KEY_ID=xxx && \
export AWS_SECRET_ACCESS_KEY=xx && \
export AWS_DEFAULT_REGION=us-west-2 && \
export BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0 && \
./deploy-to-lightsail.sh
```

## Step 3: Wait 10-15 Minutes

The script will automatically:
- ✅ Build Docker image
- ☁️ Create Lightsail container service
- 📤 Push image to AWS
- 🚀 Deploy backend
- 🏗️ Build and deploy frontend

## Step 4: Get Your URLs

When complete, you'll see:
```
╔═══════════════════════════════════════════════════════════╗
║            🎉 Deployment Complete! 🎉                     ║
╚═══════════════════════════════════════════════════════════╝

📋 Deployment Summary:
   Backend URL:  https://skyrchitect-backend.xxxxx.us-west-2.cs.amazonlightsail.com
   Frontend URL: http://skyrchitect-frontend-us-west-2.s3-website-us-west-2.amazonaws.com
```

Copy these URLs for your hackathon submission!

---

## If Something Goes Wrong

See [DEPLOY_NOW.md](DEPLOY_NOW.md) for manual deployment steps and troubleshooting.

**Most common issue**: Docker not running
- **Fix**: Make sure Docker Desktop is fully started before running the script

---

**That's it!** Just run the command above and wait. The script handles everything automatically.
