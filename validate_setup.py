# validate_setup.py
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

def validate():
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key or api_key == "your_deepseek_api_key_here":
        print("❌ Error: DEEPSEEK_API_KEY is not set in .env")
        return False
    
    print("✅ DEEPSEEK_API_KEY found.")
    
    try:
        llm = ChatOpenAI(
            model="deepseek-chat",
            openai_api_key=api_key,
            openai_api_base="https://api.deepseek.com/v1"
        )
        res = llm.invoke("Test connection. Reply with 'OK'.")
        print(f"✅ LLM Response: {res.content}")
        return True
    except Exception as e:
        print(f"❌ LLM Connection Failed: {str(e)}")
        return False

if __name__ == "__main__":
    validate()
