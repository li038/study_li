# agent_setup.py
from langchain.agents import initialize_agent, AgentType

def create_agent(tools, llm):
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )
    return agent
