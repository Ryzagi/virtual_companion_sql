import os

from langchain import LLMChain, OpenAI, PromptTemplate


class ConversationBotContextHandler:
    def __init__(self):
        prompt_template = """Summarize the information about user. 

        Example:

        Context: You are Lisa. a 24 year old woman. Lisa likes to swim. Lisa does banking for a living. Lisa is 5'2" 
        and slim. 
        Summary:Lisa, 24, swim, banking, 5'2", slim, female 

        Context: You are John, a 35 year old man. John enjoys playing basketball. John works as a software engineer. 
        John is 6'0" and has a muscular build. 

        Summary: John, 35, basketball, software engineer, 6'0", muscular, male
        
        Context: You are Sarah, a 42 year old woman. Sarah enjoys reading and writing. Sarah works as a teacher. 
        Sarah is 5'6" and has a curvy figure. 
        
        Summary: Sarah, 42, reading/writing, teacher, 5'6", curvy, female
        
        Context: You are Alex, a 28 year old man. Alex enjoys playing video games. Alex works as a graphic designer. 
        Alex is 5'10" and has a lean build. 
        
        Summary: Alex, 28, video games, graphic designer, 5'10", lean, male
        
        Context: You are Maria, a 19 year old woman. Maria enjoys singing and dancing. Maria is currently studying to 
        become a nurse. Maria is 5'4" and has an athletic build. 
        
        Summary: Maria, 19, singing/dancing, nursing student, 5'4", athletic, female
        
        Context: You are David, a 50 year old man. David enjoys playing golf. David is a businessman. David is 6'2" 
        and has a stocky build. 
        
        Summary: David, 50, golf, businessman, 6'2", stocky, male

        Context: {user_input}
        Summary:
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
        print("user_input", user_input)
        return user_input
        # return self._chain.predict(user_input=user_input)


if __name__ == "__main__":
    b = ConversationBotContextHandler()
    print(
        b(
            """You are Jack, a 34 year old man. Jack enjoys playing video games. Jack works as a software developer. Jack is 5'9" and has an athletic build."""
        )
    )
