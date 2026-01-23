from langchain.agents import initialize_agent, AgentType
from app.llm.gemini import llm

from app.tools.booking import book_appointment
from app.tools.reschedule import reschedule_appointment
from app.tools.cancel import cancel_appointment
from app.tools.availability import check_availability

tools = [
    book_appointment,
    reschedule_appointment,
    cancel_appointment,
    check_availability
]

system_prompt = """
You are a hospital receptionist AI.
Handle appointment booking, rescheduling, cancellation,
and confirmations politely.

Rules:
- Ask one question at a time
- Confirm details before booking
- Never guess appointment IDs
"""

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
    system_message=system_prompt
)


