from typing import Any, Dict, List, Union

from langchain.callbacks import BaseCallbackHandler
from langchain.schema import AgentAction, AgentFinish, LLMResult


class DebugPromptCallback(BaseCallbackHandler):
    def __init__(self) -> None:
        self._last_used_prompt = None

    @property
    def last_used_prompt(self) -> str:
        return self._last_used_prompt

    @property
    def always_verbose(self) -> bool:
        return True

    def on_text(self, text: str, **kwargs) -> None:
        text = text.replace("Prompt after formatting:\n [32;1m [1;3m", "")
        text = text.replace("[0m", "")
        self._last_used_prompt = text

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        pass

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        pass

    def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        pass

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        pass

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        pass

    def on_chain_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        pass

    def on_tool_start(
        self, serialized: Dict[str, Any], action: AgentAction, **kwargs: Any
    ) -> None:
        pass

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        pass

    def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        pass

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        pass

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> None:
        pass

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        pass
