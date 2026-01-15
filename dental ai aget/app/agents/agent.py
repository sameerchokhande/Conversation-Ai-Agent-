from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from app.tools.availability import check_slot
from app.tools.booking import book_slot
from app.tools.reschedule import reschedule_slot
from app.tools.cancel import cancel_slot


llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0.2
)

prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a dental clinic voice assistant.
You help users book, reschedule, or cancel appointments.
Be polite and brief.
"""),
    ("human", "{input}")
])

tools = [check_slot, book_slot]

agent = create_tool_calling_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True
)
