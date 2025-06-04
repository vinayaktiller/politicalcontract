import requests
import jwt
import urllib
import os
import logging
from dotenv import load_dotenv
from prometheus_client import Counter

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Prometheus metric to track authentication attempts
auth_attempts = Counter('auth_attempts', 'Total number of authentication requests')

def get_id_token_with_code_method_1(code):
    """
    Fetches the ID token from Google OAuth using the provided authorization code.

    This method sends a request to Google's OAuth2 token endpoint, exchanging
    the `code` for an ID token. The token is then decoded for user details.

    Args:
        code (str): The authorization code obtained from the frontend.

    Returns:
        dict | None: The decoded ID token containing user details, or None if the request fails.
    """
    redirect_uri = "postmessage"
    token_endpoint = "https://oauth2.googleapis.com/token"
    payload = {
        'code': code,
        'client_id': os.getenv('google_clientid'),
        'client_secret': os.getenv('google_client_secret'),
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }

    body = urllib.parse.urlencode(payload)
    headers = {
        'content-type': 'application/x-www-form-urlencoded',
    }

    # Logging and Prometheus metrics
    logger.info("Attempting to fetch ID token using authorization code.")
    auth_attempts.inc()

    response = requests.post(token_endpoint, data=body, headers=headers)
    if response.ok:
        id_token = response.json().get('id_token')
        decoded_token = jwt.decode(id_token, options={"verify_signature": False})
        logger.info(f"Successfully retrieved ID token for user: {decoded_token.get('email')}")
        return decoded_token
    else:
        logger.error(f"Failed to retrieve ID token: {response.json()}")
        return None
