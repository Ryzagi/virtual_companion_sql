from pathlib import Path

from converbot.core import GPT3Conversation
from converbot.prompt.prompt import ConversationPrompt


def create_conversation(
    prompt: ConversationPrompt,
    tone: str,
    config_path: Path,
) -> GPT3Conversation:
    """
    Create a conversation from a prompt and a configuration file.

    Args:
        prompt: The prompt for the conversation.
        tone: The tone of the chatbot.
        config_path: The path to the configuration file.
    """
    conversation = GPT3Conversation.from_config_file(prompt, config_path)
    conversation.set_tone(tone)
    return conversation
