""" Azure AI Foundry Agent that generates an outline """

from a2a.helpers import new_task_from_user_message, new_text_part
from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import AgentCard, TaskState
from outline_agent.agent import OutlineAgent, create_foundry_outline_agent

# An AgentExecutor that runs Azure AI Foundry-based agents. Adapted from the ADK agent executor pattern.
class OutlineAgentExecutor(AgentExecutor):

    def __init__(self, card: AgentCard):
        self._card = card
        self._foundry_agent: OutlineAgent | None = None

    async def _get_or_create_agent(self) -> OutlineAgent:
        if not self._foundry_agent:
            self._foundry_agent = await create_foundry_outline_agent()
        return self._foundry_agent

    async def _process_request(self, context: RequestContext, task_updater: TaskUpdater) -> None:
        # Process a user request through the Foundry agent

        try:
            # Retrieve message text from the A2A parts
            user_message = context.get_user_input()

            # Get the outline agent
            agent = await self._get_or_create_agent()

            # Update the task status
            await task_updater.update_status(
                TaskState.TASK_STATE_WORKING,
                message=task_updater.new_agent_message(
                    [new_text_part('Outline Agent is processing your request...')]
                ),
            )

            # Run the conversation
            responses = await agent.run_conversation(user_message)

            # Update the task with responses
            for response in responses:
                await task_updater.update_status(
                    TaskState.TASK_STATE_WORKING,
                    message=task_updater.new_agent_message([new_text_part(response)]),
                )

            # Mark the task as complete
            final_message = responses[-1] if responses else 'Task completed.'
            await task_updater.complete(
                message=task_updater.new_agent_message([new_text_part(final_message)])
            )

        except Exception as e:
            print(f'Outline Agent failed to process the request: {e}')
            await task_updater.failed(
                message=task_updater.new_agent_message(
                    [new_text_part('Outline Agent failed to process the request.')]
                )
            )

    async def execute(self, context: RequestContext, event_queue: EventQueue):

        # A2A 1.x: the Task must be the first event, before any status update
        await event_queue.enqueue_event(new_task_from_user_message(context.message))

        # Create task updater
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.submit()

        # Start working
        await updater.start_work()

        # Process the request
        await self._process_request(context, updater)

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        print(f'Outline Agent: Cancelling execution for context {context.context_id}')

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.failed(
            message=updater.new_agent_message([new_text_part('Task cancelled by user')])
        )

def create_foundry_agent_executor(card: AgentCard) -> OutlineAgentExecutor:
    return OutlineAgentExecutor(card)
