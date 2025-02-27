import os
import logging
import oauthlib.oauth2.rfc6749.errors
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from fastapi import HTTPException

# Function to get the access token
def get_access_token(token_url, api_url): 
    # Function to get environment variable
    def get_env(key, default=None):
        value = os.environ.get(key, default)
        if value == 'True' or value == 'true':
            value = True
        elif value == 'False' or value == 'false':
            value = False
        return value

    client_id = (get_env("CLIENT_ID"))
    client_secret = (get_env("CLIENT_SECRET"))

    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)

    try:
        token = oauth.fetch_token(token_url=token_url, client_id=client_id, client_secret=client_secret)
        return token['access_token'] 
    except oauthlib.oauth2.rfc6749.errors.OAuth2Error as e:
        logging.error(f"Error fetching access token: {e}")
        raise HTTPException(status_code=500, detail="Error fetching access token")
    except Exception as e:
        logging.error(f"Error fetching access token: {e}")
        raise HTTPException(status_code=500, detail="Error fetching access token")
