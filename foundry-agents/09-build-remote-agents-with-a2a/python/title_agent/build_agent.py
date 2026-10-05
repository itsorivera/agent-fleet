from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from ref_app import AgentSpec
from title_agent.agent_executor import create_foundry_agent_executor as create_title_executor


def build_agent(base_url: str, port: int) -> AgentSpec:
    """Construye el agente de title."""
    skills = [
        AgentSkill(
            id='generate_blog_title',
            name='Generate Blog Title',
            description='Generates a blog title based on a topic',
            tags=['title'],
            examples=['Can you give me a title for this article?'],
        ),
    ]
    card = AgentCard(
        name='Microsoft Foundry Title Agent',
        description='An intelligent title generator agent powered by Foundry.',
        supported_interfaces=[AgentInterface(url=f'http://{base_url}:{port}')],
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(),
        skills=skills,
    )
    executor = create_title_executor(card)
    handler = DefaultRequestHandler(agent_executor=executor, agent_card=card, task_store=InMemoryTaskStore())
    return AgentSpec(agent_id='title', card=card, handler=handler)
