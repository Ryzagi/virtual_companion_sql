from dataclasses import dataclass

from converbot.config.base import OpenAIModelConfig
from converbot.constants import DEFAULT_FRIENDLY_TONE


@dataclass
class GPT3ConversationConfig(OpenAIModelConfig):
    """
    The configuration for the romantic conversation.

    Args:
        summary_buffer_memory_max_token_limit: The maximum number of tokens to store in the summary buffer.
    """

    tone: str = DEFAULT_FRIENDLY_TONE
    summary_buffer_memory_max_token_limit: int = 1000
