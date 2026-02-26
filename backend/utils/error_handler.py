# backend/utils/error_handler.py
# Centralized error handling and logging
# Owner: Manoj RS
# See: Detailed_Implementation_Guide.md Section 7

import logging
import traceback

logger = logging.getLogger("SmartRuralAI")
logger.setLevel(logging.INFO)


def handle_lambda_error(func):
    """
    Decorator for Lambda handlers — catches exceptions and returns
    a standardized error response.
    """
    from backend.utils.response_helper import error_response

    def wrapper(event, context):
        try:
            return func(event, context)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            return error_response(
                message=f"Internal server error: {str(e)}",
                status_code=500
            )
    return wrapper
