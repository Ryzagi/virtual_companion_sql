import os

from langchain import LLMChain, OpenAI, PromptTemplate


class SelfieStyleHandler:
    def __init__(self):
        prompt_template = """Following in the format of those examples, please create a very short prompt that I can 
        use to make a photo-realistic portrait of this person described below. Please describe their face and 
        surroundings. 

        Example: 

        Context: 
        Name: Mike
        Age: 23
        Gender: male
        Interests: offroading, picking up chicks, drinking beers
        Profession: bartender
        Appearance: athletic build, strong arms, no beard
        Relationship status: single
        Personality: Mike is a total man's man. He loves hanging with his bros and downing beers.

        Selfie style: Professional close-up portrait photograph of a 23 year old athletic, bartending man with no facial 
        hair, strong arms, drinking a beer, ((playful and mischievous expression)), standing outside in an open field 
        with off-roading vehicles, ultra-realistic, concept art, elegant, highly detailed, intricate, sharp focus, 
        depth of field, f/1. 8, 85mm, mid-shot, (centered image composition), (professionally color graded), 
        ((bright soft diffused light)), volumetric fog, trending on Instagram, trending on Tumblr,  4k, 8k. 

        Context: {user_input}
        Selfie style:
        """
        prompt_template = PromptTemplate(
            input_variables=["user_input"], template=prompt_template
        )

        self._chain = LLMChain(
            llm=OpenAI(temperature=0.9),
            prompt=prompt_template,
            verbose=False,
        )

    def __call__(self, user_input: str) -> str:
        return self._chain.predict(user_input=user_input)
