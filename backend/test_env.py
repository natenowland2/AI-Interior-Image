import os
from dotenv import load_dotenv
import openai

def test_openai_connection():
    print("Testing OpenAI API Connection...")
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        return False
    
    print(f"API Key found: {api_key[:10]}...{api_key[-5:]}")
    
    try:
        # Configure OpenAI
        openai.api_key = api_key
        
        print("\nTesting DALL-E API...")
        # Test DALL-E API with minimal parameters
        response = openai.Image.create(
            prompt="A simple blue circle",
            n=1,
            size="1024x1024"
        )
        print("✅ DALL-E API Test Successful!")
        print("Image URL:", response['data'][0]['url'])
        return True
        
    except Exception as e:
        print("\n❌ Error testing OpenAI API:")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        
        print("\nPossible issues:")
        print("1. API key may not have DALL-E access enabled")
        print("2. Organization billing may not be set up")
        print("3. Project may not have sufficient credits")
        print("\nPlease check:")
        print("1. Visit https://platform.openai.com/account/billing to set up billing")
        print("2. Ensure DALL-E API access is enabled at https://platform.openai.com/account/limits")
        print("3. Verify API key permissions at https://platform.openai.com/api-keys")
        return False

if __name__ == "__main__":
    test_openai_connection() 