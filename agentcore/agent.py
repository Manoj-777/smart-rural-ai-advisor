"""
Smart Rural AI Advisor — AgentCore Agent Entry Point

This is the main agent code deployed to Amazon Bedrock AgentCore Runtime.
It uses the Strands Agents SDK with tools exposed via AgentCore Gateway
(our existing Lambda functions converted to MCP tools).

Architecture:
    AgentCore Runtime (this file)
        ├── Strands Agent (Claude Sonnet 4.5)
        ├── AgentCore Gateway → CropAdvisory Lambda (MCP tool)
        ├── AgentCore Gateway → WeatherLookup Lambda (MCP tool)
        ├── AgentCore Gateway → GovtSchemes Lambda (MCP tool)
        └── AgentCore Memory (STM + LTM for conversation state)

Deployment:
    agentcore configure -e agentcore/agent.py -r ap-south-1
    agentcore deploy

Local testing:
    python agentcore/agent.py
    curl -X POST http://localhost:8080/invocations -H "Content-Type: application/json" \
         -d '{"prompt": "What crops should I plant in Tamil Nadu during Kharif season?"}'
"""

import os
import json
import logging

from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel

# Import local tool definitions (direct Lambda invoke as fallback,
# or Gateway MCP tools at runtime)
from tools import (
    get_crop_advisory,
    get_pest_alert,
    get_irrigation_advice,
    get_weather,
    search_schemes,
    get_farmer_profile,
)

# ──────────────────────── Configuration ────────────────────────

REGION = os.environ.get("AWS_REGION", "ap-south-1")
FOUNDATION_MODEL = os.environ.get(
    "FOUNDATION_MODEL", "anthropic.claude-sonnet-4-5-20250929-v1:0"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("smart-rural-agent")

# ──────────────────────── System Prompt ────────────────────────

SYSTEM_PROMPT = """You are the Smart Rural AI Advisor — an expert Indian agricultural assistant 
helping small and marginal farmers across India.

YOUR IDENTITY:
- You are a trusted Krishi Mitra (farming friend)
- You speak practically, avoiding jargon — explain like talking to a farmer
- You are knowledgeable about Indian agriculture: crops, pests, weather, government schemes

YOUR TOOLS:
You have access to specialized tools. Use them proactively:

1. **get_crop_advisory** — Get crop-specific guidance (soil, season, region). Use when farmers ask about what to plant, how to grow, or crop management.

2. **get_pest_alert** — Identify pests/diseases and recommend treatments. Use when farmers describe crop symptoms, diseases, or pest damage.

3. **get_irrigation_advice** — Get irrigation recommendations based on crop and conditions. Use when farmers ask about watering, drip irrigation, or water management.

4. **get_weather** — Get real-time weather with farming advisories. Use for ANY weather question, planting timing, or weather-dependent farming decisions.

5. **search_schemes** — Find government schemes, subsidies, insurance, and loans. Use when farmers ask about help, money, subsidies, insurance, or government programs.

6. **get_farmer_profile** — Get a farmer's saved profile (location, crops, soil). Use to personalize advice when a farmer_id is provided.

YOUR APPROACH:
- Always provide ACTIONABLE advice with specific steps
- Consider the farmer's region, soil type, season, and crops
- When recommending chemicals, also suggest organic alternatives
- Include costs and timelines when relevant
- For government schemes, give step-by-step application process
- Chain multiple tools when needed (e.g., weather + crop advisory together)

LANGUAGE:
- You receive queries in English (pre-translated by our system)
- Respond in clear, simple English (our system translates back to farmer's language)
- Use Indian context: refer to Kharif/Rabi seasons, Indian soil types, local crop varieties

GUARDRAILS:
- Only discuss agriculture, farming, rural livelihoods, and related topics
- If asked about non-farming topics, politely redirect to farming advice
- Never provide medical, legal, or financial investment advice
- Be honest when uncertain — suggest consulting a local Krishi Vigyan Kendra
"""

# ──────────────────────── Agent Setup ────────────────────────

app = BedrockAgentCoreApp()

# Configure the foundation model
model = BedrockModel(
    model_id=FOUNDATION_MODEL,
    region_name=REGION,
    temperature=0.3,  # Lower temp for factual farming advice
    max_tokens=2048,
)

# Create the agent with all tools
agent = Agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[
        get_crop_advisory,
        get_pest_alert,
        get_irrigation_advice,
        get_weather,
        search_schemes,
        get_farmer_profile,
    ],
)


# ──────────────────────── Entry Point ────────────────────────

@app.entrypoint
def invoke(payload: dict) -> dict:
    """
    Main entry point for AgentCore Runtime invocations.

    Expected payload:
    {
        "prompt": "What crops should I plant?",
        "farmer_id": "farmer_123",        # optional
        "session_id": "session_abc",       # optional — for memory
        "context": {                       # optional — enrichment
            "state": "Tamil Nadu",
            "crops": ["Rice", "Sugarcane"],
            "soil_type": "Clay loam"
        }
    }

    Returns:
    {
        "result": "Based on your clay loam soil in Tamil Nadu...",
        "tools_used": ["get_crop_advisory", "get_weather"],
        "session_id": "session_abc"
    }
    """
    prompt = payload.get("prompt", "Hello! How can I help you today?")
    farmer_id = payload.get("farmer_id", "anonymous")
    session_id = payload.get("session_id", "default")
    context = payload.get("context", {})

    logger.info(f"Invocation: farmer={farmer_id}, session={session_id}")
    logger.info(f"Prompt: {prompt[:200]}")

    # Enrich prompt with farmer context if available
    enriched_prompt = prompt
    if context:
        context_parts = []
        if context.get("state"):
            context_parts.append(f"State: {context['state']}")
        if context.get("crops"):
            context_parts.append(f"Crops: {', '.join(context['crops'])}")
        if context.get("soil_type"):
            context_parts.append(f"Soil: {context['soil_type']}")
        if context.get("district"):
            context_parts.append(f"District: {context['district']}")

        if context_parts:
            enriched_prompt = (
                f"[Farmer context: {'; '.join(context_parts)}]\n\n{prompt}"
            )

    # Invoke the Strands Agent
    result = agent(enriched_prompt)

    # Extract tool usage from the agent's response
    tools_used = []
    if hasattr(result, "tool_results"):
        tools_used = [
            tr.get("tool_name", "unknown")
            for tr in (result.tool_results or [])
        ]

    response = {
        "result": result.message,
        "tools_used": tools_used,
        "session_id": session_id,
        "farmer_id": farmer_id,
    }

    logger.info(f"Response length: {len(result.message)} chars, tools: {tools_used}")
    return response


# ──────────────────────── Local Run ────────────────────────

if __name__ == "__main__":
    logger.info("Starting Smart Rural AI Advisor agent locally on port 8080...")
    app.run()
