from langchain.agents import initialize_agent, Tool
from langchain_community.llms import Ollama
from langchain.agents.agent_types import AgentType

llm = Ollama(model="llama3")

def get_weather(location):
    return f"{location} is sunny today ☀️"  # dummy response

tools = [
    Tool(
        name="WeatherAPI",
        func=get_weather,
        description="Gets weather for a given location"
    )
]

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)

agent.run("What's the weather in Hyderabad?")
