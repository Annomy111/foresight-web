"""
Netlify Functions wrapper for FastAPI backend
Converts FastAPI application to Netlify serverless function
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = str(Path(__file__).parent.parent.parent / "backend")
sys.path.insert(0, backend_path)

# Import FastAPI app
from main import app

# Mangum adapter for serverless
from mangum import Mangum

# Create the handler
handler = Mangum(app, lifespan="off")

def main(event, context):
    """Main handler for Netlify Functions"""
    # Adapt event for AWS Lambda compatibility
    if "httpMethod" in event:
        event["requestContext"] = event.get("requestContext", {})
        event["requestContext"]["http"] = {
            "method": event["httpMethod"],
            "path": event["path"]
        }

    # Call the handler
    return handler(event, context)