from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

def llm():
    load_dotenv()
    API_KEY = os.getenv("GOOGLE_API_KEY")
    if not API_KEY:
        raise ValueError(
            "GOOGLE_API_KEY not found. Check that a .env file exists in the "
            "working directory and contains GOOGLE_API_KEY=<your_key>."
        )
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=API_KEY)
    return llm