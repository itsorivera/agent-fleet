import asyncio
import os
from typing import cast
from dotenv import load_dotenv

# Add references
from agent_framework import Message
from agent_framework.foundry import FoundryChatClient
from agent_framework.orchestrations import SequentialBuilder
from azure.identity import AzureCliCredential


load_dotenv()

async def main():
    # Agent instructions
    summarizer_instructions="""
    Summarize the customer's feedback in one short sentence. Keep it neutral and concise.
    Example output:
    App crashes during photo upload.
    User praises dark mode feature.
    """

    classifier_instructions="""
    Classify the feedback as one of the following: Positive, Negative, or Feature request.
    """

    action_instructions="""
    Based on the summary and classification, suggest the next action in one short sentence.
    Example output:
    Escalate as a high-priority bug for the mobile team.
    Log as positive feedback to share with design and marketing.
    Log as enhancement request for product backlog.
    """

    # Create the chat client
    credential = AzureCliCredential() # this object will allow your code to authenticate to your Azure account
    chat_client = FoundryChatClient( # this object connects to your Foundry project using the endpoint and model deployment name from the .env configuration.
        credential=credential,
        project_endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT"),
        model=os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME"),
    )

    # Create agents
    summarizer_agent = chat_client.as_agent(
        name="summarizer",
        instructions=summarizer_instructions,
    )

    classifier_agent = chat_client.as_agent(
        name="classifier",
        instructions=classifier_instructions,
    )

    action_agent = chat_client.as_agent(
        name="action",
        instructions=action_instructions,
    )

    ##############3 CREATE SEQUENTIAL ORCHESTRATION #################
    # Initialize the current feedback
    feedback="""
    I use the dashboard every day to monitor metrics, and it works well overall. 
    But when I'm working late at night, the bright screen is really harsh on my eyes. 
    If you added a dark mode option, it would make the experience much more comfortable.
    """

    # Build sequential orchestration
    # The agents will process the feedback in the order they are added to the orchestration. The output_from="all" parameter ensures that outputs from all agents are collected.
    workflow = SequentialBuilder(
        participants=[summarizer_agent, classifier_agent, action_agent],
        output_from="all",
    ).build()

    # Run and collect outputs
    # This code runs the orchestration and collects the output from each of the participating agents.
    result = await workflow.run(f"Customer feedback: {feedback}")
    outputs = result.get_outputs()


    # Display outputs
    # This code formats and displays the messages from the workflow outputs you collected from the orchestration.
    i = 1
    for response in outputs:
        for msg in cast(list[Message], response.messages):
            name = msg.author_name or ("assistant" if msg.role == "assistant" else "user")
            print(f"{'-' * 60}\n{i:02d} [{name}]\n{msg.text}")
            i += 1

    
if __name__ == "__main__":
    asyncio.run(main())