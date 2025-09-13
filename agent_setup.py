# agent_setup.py
from langchain.agents import initialize_agent, AgentType

def create_agent(tools, llm):
    """创建代理，兼容新旧版本
    
    注意：initialize_agent已显示弃用警告，建议新项目使用LangGraph
    但当前实现仍保持兼容性
    """
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )
    return agent
