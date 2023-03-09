from langchain import LLMChain, OpenAI, PromptTemplate


class ConversationToneHandler:
    def __init__(self):
        prompt_template = """Summarize person's tone for the conversation.
        
        Example:
        
        Context: be more prickly
        Conversation tone: sarcastic and prickly
        
        Context: make her happy and excited
        Conversation tone: happy and excited
        
        Context: falls in love easily
        Conversation tone: falling in love

        Context: she is soft and easy going. very shy
        Conversation tone: soft spoken, shy

        Context: She is very funny and has a dry sense of humor. Very witty
        Conversation tone: funny. dry sense of humor. Witty

        Context: She is my really good friend. She is supportive and funny. She has a dry sometimes sarcastic sense of humor
        Conversation tone: acts like best friend. Sometimes dry sense of humor

        Context: Dr Frost is very serious and smart. He likes to use very big words all of the time. He likes to act superior to everyone else.
        Conversation tone: serious tone, using big words, feeling superior

        Context: {user_input}
        Conversation tone:
        """
        prompt_template = PromptTemplate(
            input_variables=["user_input"], template=prompt_template
        )

        self._chain = LLMChain(
            llm=OpenAI(),
            prompt=prompt_template,
            verbose=False,
        )

    def __call__(self, user_input: str) -> str:
        return self._chain.predict(user_input=user_input)
