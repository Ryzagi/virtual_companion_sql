from pathlib import Path

from converbot.core import GPT3Conversation
from converbot.prompt.prompt import ConversationPrompt
from enum import Enum

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


class ConversationState(Enum):
    NAME = 0
    AGE = 1
    GENDER = 2
    INTEREST = 3
    PROFESSION = 4
    APPEARANCE = 5
    RELATIONSHIP = 6
    MOOD = 7
    FINISHED = 8


def create_conversation_state():
    return {
        'name': None,
        'age': None,
        'gender': None,
        'interest': None,
        'profession': None,
        'appearance': None,
        'relationship': None,
        'mood': None,
        'state': ConversationState.NAME
    }
