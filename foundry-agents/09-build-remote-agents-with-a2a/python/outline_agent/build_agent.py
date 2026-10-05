from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from ref_app import AgentSpec
from outline_agent.agent_executor import create_foundry_agent_executor as create_outline_executor


def build_agent(base_url: str, port: int) -> AgentSpec:
    """Construye el agente de outline."""
    skills = [
        AgentSkill(
            id='generate_outline',
            name='Generate Outline',
            description='Generates an outline based on a topic',
            tags=['outline'],
            examples=['Can you give me an outline for this article?'],
        ),
    ]
    card = AgentCard(
        name='AI Foundry Outline Agent',
        description='An intelligent outline generator agent powered by Azure AI Foundry.',
        supported_interfaces=[AgentInterface(url=f'http://{base_url}:{port}')],
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=skills,
    )
    executor = create_outline_executor(card)
    handler = DefaultRequestHandler(agent_executor=executor, agent_card=card, task_store=InMemoryTaskStore())
    return AgentSpec(agent_id='outline', card=card, handler=handler)

