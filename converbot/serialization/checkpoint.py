import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from converbot.config.gptconversation import GPT3ConversationConfig
from io import open

@dataclass
class GPT3ConversationCheckpoint:
    """
    A checkpoint for a GPT-3 conversation.

    Args:
        config: The configuration for the GPT-3 conversation.
        prompt_template: The template for the prompt.
        prompt_user_name: The name of the user.
        prompt_chatbot_name: The name of the chatbot.
        memory_buffer: The buffer for the memory.
        memory_moving_summary_buffer: The moving summary buffer for the memory.
    """

    config: GPT3ConversationConfig
    prompt_template: str
    prompt_user_name: str
    prompt_chatbot_name: str
    memory_buffer: List[str]
    memory_moving_summary_buffer: str
    bot_description: Optional[str] = None

    @classmethod
    def from_json(cls, file_path: Path) -> "GPT3ConversationCheckpoint":
        """
        Load a checkpoint from a json file.

        Args:
            file_path: Path to JSON file.
        """
        data = json.loads(file_path.read_text())
        data["config"] = GPT3ConversationConfig(**data["config"])
        return cls(**data)

    def to_json(self, save_path: Path) -> None:
        """
        Save the checkpoint to a json file.

        Args:
            save_path: The path to save the configuration.
        """
        self.config = self.config.__dict__  # noqa
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self.__dict__, f, indent=4, ensure_ascii=False)
        self.config = GPT3ConversationConfig(**self.config)  # noqa
