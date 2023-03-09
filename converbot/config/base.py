import json
from dataclasses import dataclass
from pathlib import Path

from converbot.constants import DEFAULT_CONFIG_PATH


@dataclass
class OpenAIModelConfig:
    """
    Class for storing OpenAI model configuration.
    """

    model: str = "text-davinci-003"
    max_tokens: int = 256
    temperature: float = 0.9
    top_p: int = 1
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    best_of: int = 1

    @classmethod
    def from_json(
        cls, file_path: Path = DEFAULT_CONFIG_PATH
    ) -> "OpenAIModelConfig":
        """
        Load OpenAI model configuration from JSON file.

        Args:
            file_path: Path to JSON file.
        """
        data = json.loads(file_path.read_text())
        return cls(**data)

    def to_json(self, save_path: Path) -> None:
        """
        Save the configuration to a json file.

        Args:
            save_path: The path to save the configuration.
        """
        with open(save_path, "w") as f:
            json.dump(self.__dict__, f, indent=4)
