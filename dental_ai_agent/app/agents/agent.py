from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType
from langchain.prompts import ChatPromptTemplate

from app.tools.availability import check_slot
from app.tools.booking import book_slot
from app.tools.cancel import cancel_slot
from app.tools.reschedule import reschedule_slot



# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0.2
)

# Define tools
tools = [
    check_slot,
    book_slot,
    reschedule_slot,
    cancel_slot
]

# Create agent executor (STABLE API)
agent_executor = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)
