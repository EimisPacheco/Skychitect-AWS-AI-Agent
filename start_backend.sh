#!/bin/bash
# Start Skyrchitect AI Backend Server

echo "🚀 Starting Skyrchitect AI Backend..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "   Please create .env with AWS credentials"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check AWS credentials
if [ -z "$AWS_ACCESS_KEY_ID" ]; then
    echo "❌ Error: AWS_ACCESS_KEY_ID not set in .env"
    exit 1
fi

echo "✓ Environment variables loaded"
echo "✓ AWS Region: $AWS_DEFAULT_REGION"
echo "✓ Bedrock Model: $BEDROCK_MODEL_ID"
echo ""

# Start the server
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd "$(dirname "$0")"
python3 -m uvicorn backend.api.main:app --reload --port 8000 --host 0.0.0.0
