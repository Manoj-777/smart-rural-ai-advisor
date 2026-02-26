# backend/lambdas/govt_schemes/handler.py
# AgentCore Tool: Government scheme lookup
# Owner: Manoj RS
# Endpoint: GET /schemes
# See: Detailed_Implementation_Guide.md Section 9

import json
import logging
from utils.response_helper import (
    success_response, error_response,
    is_bedrock_event, parse_bedrock_params, bedrock_response, bedrock_error_response
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Curated scheme data (could also be in DynamoDB)
SCHEMES = {
    "pm_kisan": {
        "name": "PM-KISAN",
        "full_name": "Pradhan Mantri Kisan Samman Nidhi",
        "benefit": "₹6,000 per year (₹2,000 every 4 months)",
        "eligibility": "All landholding farmer families",
        "how_to_apply": "1. Visit nearest Common Service Centre (CSC)\n2. OR Register online at https://pmkisan.gov.in\n3. Documents needed: Aadhaar card, bank account, land records\n4. Verification by state/district officials",
        "helpline": "011-23381092",
        "website": "https://pmkisan.gov.in"
    },
    "pmfby": {
        "name": "PMFBY",
        "full_name": "Pradhan Mantri Fasal Bima Yojana",
        "benefit": "Crop insurance at 2% premium (Kharif), 1.5% (Rabi)",
        "eligibility": "All farmers growing notified crops",
        "how_to_apply": "1. Through your bank (auto-enrolled if crop loan exists)\n2. Through Common Service Centre\n3. Online at https://pmfby.gov.in\n4. Deadline: Before crop sowing season cutoff date",
        "helpline": "1800-180-1551",
        "website": "https://pmfby.gov.in"
    },
    "kcc": {
        "name": "KCC",
        "full_name": "Kisan Credit Card",
        "benefit": "Short-term crop loan at 4% effective interest (with subsidy)",
        "eligibility": "All farmers — individual, joint, tenant, sharecroppers",
        "how_to_apply": "1. Visit any bank branch (SBI, cooperative, regional rural bank)\n2. Submit: Application form + land records + ID proof + photos\n3. Approved in 15 days\n4. Card valid for 5 years with annual renewal",
        "helpline": "1800-180-1551",
        "website": "https://pmkisan.gov.in/KCC"
    },
    "soil_health_card": {
        "name": "Soil Health Card",
        "full_name": "Soil Health Card Scheme",
        "benefit": "Free soil testing + fertilizer recommendations",
        "eligibility": "All farmers",
        "how_to_apply": "1. Visit nearest soil testing lab or Krishi Vigyan Kendra\n2. Provide soil sample\n3. Card issued within 2 weeks",
        "helpline": "1800-180-1551",
        "website": "https://soilhealth.dac.gov.in"
    },
    "pmksy": {
        "name": "PMKSY",
        "full_name": "Pradhan Mantri Krishi Sinchayee Yojana",
        "benefit": "55% subsidy on micro-irrigation (drip/sprinkler)",
        "eligibility": "All farmers — higher subsidy for small/marginal farmers",
        "how_to_apply": "1. Apply through state agriculture department\n2. OR through district horticulture office\n3. Submit land records + bank details",
        "helpline": "1800-180-1551",
        "website": "https://pmksy.gov.in"
    },
    "e_nam": {
        "name": "eNAM",
        "full_name": "National Agriculture Market",
        "benefit": "Online trading platform — better prices, transparent bidding",
        "eligibility": "All farmers with produce to sell",
        "how_to_apply": "1. Register at https://enam.gov.in\n2. Visit nearest eNAM mandi\n3. Get quality tested and listed",
        "helpline": "1800-270-0224",
        "website": "https://enam.gov.in"
    },
    "pkvy": {
        "name": "PKVY",
        "full_name": "Paramparagat Krishi Vikas Yojana",
        "benefit": "₹50,000/hectare over 3 years for organic farming",
        "eligibility": "Groups of 50+ farmers with 50 acres",
        "how_to_apply": "1. Form a farmer group (50+ farmers)\n2. Apply through district agriculture officer\n3. Get organic certification support",
        "helpline": "1800-180-1551",
        "website": "https://pgsindia-ncof.gov.in"
    },
    "nfsm": {
        "name": "NFSM",
        "full_name": "National Food Security Mission",
        "benefit": "Subsidized seeds, fertilizers, and farm machinery",
        "eligibility": "Farmers in identified districts growing rice, wheat, pulses, coarse cereals",
        "how_to_apply": "1. Contact block agriculture officer\n2. Register under NFSM scheme\n3. Receive subsidized inputs",
        "helpline": "1800-180-1551",
        "website": "https://nfsm.gov.in"
    },
    "agriculture_infra_fund": {
        "name": "AIF",
        "full_name": "Agriculture Infrastructure Fund",
        "benefit": "3% interest subvention on loans up to ₹2 crore",
        "eligibility": "Farmers, FPOs, PACS, startups, agri-entrepreneurs",
        "how_to_apply": "1. Apply online at https://agriinfra.dac.gov.in\n2. Loan through any scheduled bank\n3. For: cold storage, warehouses, processing units",
        "helpline": "1800-180-1551",
        "website": "https://agriinfra.dac.gov.in"
    }
}


def lambda_handler(event, context):
    """Returns government scheme information."""
    try:
        # Handle CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return success_response({}, message='OK')

        from_bedrock = is_bedrock_event(event)

        if from_bedrock:
            params = parse_bedrock_params(event)
            scheme_name = params.get('scheme_name', params.get('query', 'all')).lower()
            farmer_state = params.get('farmer_state', '')
        elif 'parameters' in event:
            # Legacy Bedrock format (fallback)
            params = {p['name']: p['value'] for p in event['parameters']}
            scheme_name = params.get('scheme_name', 'all').lower()
            farmer_state = params.get('farmer_state', '')
        else:
            # API Gateway GET: read from query string; POST: read from body
            qs = event.get('queryStringParameters') or {}
            if qs:
                scheme_name = qs.get('name', qs.get('search', 'all')).lower()
                farmer_state = qs.get('state', '')
            else:
                body = json.loads(event.get('body', '{}')) if event.get('body') else {}
                scheme_name = body.get('scheme_name', 'all').lower()
                farmer_state = body.get('farmer_state', '')

        if scheme_name == 'all':
            result = SCHEMES
        elif scheme_name in SCHEMES:
            result = SCHEMES[scheme_name]
        else:
            # Search by keyword across name, full_name, and benefit
            result = {k: v for k, v in SCHEMES.items()
                     if scheme_name in v['name'].lower()
                     or scheme_name in v['full_name'].lower()
                     or scheme_name in v.get('benefit', '').lower()}

        result_data = {
            'schemes': result,
            'note': 'Contact Kisan Call Centre at 1800-180-1551 for more details'
        }

        if from_bedrock:
            return bedrock_response(result_data, event)
        return success_response(result_data)

    except Exception as e:
        logger.error(f"Schemes error: {str(e)}")
        if is_bedrock_event(event):
            return bedrock_error_response(str(e), event)
        return error_response(str(e), 500)
