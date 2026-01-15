
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings

llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    temperature=0.2,
    google_api_key=settings.GOOGLE_API_KEY
)
