import requests 
import json 

# Function to chat with the Veolia Secure GPT API
def chat_with_api(prompt: str, access_token: str, client_email: str,
                  temperature: float = 0.1, top_p: int = 1,
                  model: str = "gemini-pro-vision-1.5"):
                
    api_url = 'https://api.veolia.com/llm/veoliasecuregpt/v1/answer'

    headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
    }

    data = {
    "useremail": f"{client_email}",

    "history": [
        {
            "role": "user",
            "content": prompt
        }
    ],
    "temperature": temperature,
    "top_p": top_p,
    "model": model,
}
    response = requests.post(api_url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        return (response.json())
    else:
        raise Exception(f"API call failed with status code {response.status_code}")
