"""Minimal agent.py - just registers an entrypoint, nothing else."""
import json
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("minimal")
logger.info("MINIMAL: Starting imports...")

from bedrock_agentcore import BedrockAgentCoreApp
logger.info("MINIMAL: BedrockAgentCoreApp imported")

def invoke(payload: dict) -> dict:
    return {"result": "Hello from minimal agent!", "agent_role": "master"}

app = BedrockAgentCoreApp()
app.entrypoint(invoke)
logger.info("MINIMAL: Entrypoint registered, ready!")

if __name__ == "__main__":
    app.run()
