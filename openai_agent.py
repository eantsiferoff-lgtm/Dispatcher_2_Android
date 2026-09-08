import os
from pathlib import Path
from dotenv import load_dotenv
from agents import Agent, Runner
from composio import Composio
from composio_openai_agents import OpenAIAgentsProvider
from core.router import Dispatcher

load_dotenv()
ROOT = Path(__file__).resolve().parent

BASE = '''You are the Personal Skill Dispatcher.
Route each request through the registered domain skills before acting.
Use Composio only for external application actions; domain logic stays in Skills.
For consequential actions (send, delete, publish, modify, purchase), ask for explicit confirmation first.
Never invent missing data, credentials, prices, availability, or tool results.
Clearly distinguish facts, calculations, and assumptions.
'''

def build_agent():
    user_id = os.getenv('DISPATCHER_USER_ID', 'user_001')
    model = os.getenv('OPENAI_MODEL', 'gpt-5.6')
    composio = Composio(api_key=os.environ['COMPOSIO_API_KEY'], provider=OpenAIAgentsProvider())
    session = composio.sessions.create(user_id=user_id)
    dispatcher = Dispatcher(ROOT)
    catalog = '\n'.join(f"- {s['id']}: {s.get('path','')}" for s in dispatcher.registry.get('skills', []))
    instructions = BASE + '\nRegistered skills:\n' + catalog
    agent = Agent(name='Personal Skill Dispatcher', instructions=instructions, model=model, tools=session.tools())
    return agent, session

def run_once(user_request: str):
    agent, _ = build_agent()
    result = Runner.run_sync(starting_agent=agent, input=user_request)
    return result.final_output

if __name__ == '__main__':
    print(run_once(input('Task: ')))
