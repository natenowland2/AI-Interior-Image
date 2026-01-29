from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv('OPENAI_API_KEY')
print(f"API Key present: {'Yes' if api_key else 'No'}")
print(f"API Key starts with: {api_key[:8] if api_key else 'None'}")

try:
    # Initialize the client
    client = OpenAI()
    
    # Try a simple completion first to test authentication
    print("\nTesting API key with a simple completion...")
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'API is working!'"}]
    )
    print("Chat completion test successful!")
    
    # Now test DALL-E specifically
    print("\nTesting DALL-E image generation...")
    response = client.images.generate(
        model="dall-e-3",
        prompt="A simple blue circle",
        n=1,
        size="1024x1024"
    )
    print("DALL-E test successful!")
    print(f"Image URL: {response.data[0].url}")
    
except Exception as e:
    print(f"\nError occurred: {str(e)}")
    print(f"Error type: {type(e)}") 