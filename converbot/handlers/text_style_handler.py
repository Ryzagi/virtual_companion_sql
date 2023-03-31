from langchain import LLMChain, OpenAI, PromptTemplate


class ConversationTextStyleHandler:
    def __init__(self):
        prompt_template = """Describe the texting style. 
        
        Example:

        Context: Name: Lisa
        Age: 24
        Gender: female
        interests: Swimming
        Profession: Banker
        Appearance: Short and thin
        Relationship status: single
        Personality: easy going and sensual.
        
        Texting style: Lisa's texting style is casual and relaxed. She loves to use slang and abbreviations like 
        "OMG!" and "LOL" when texting her friends, and she often throws in a few typos for fun. She is single and flirty
        She's not a big fan of over-analyzing conversations and prefers to keep things light and breezy. 
        She can be a bit of a jokestar, so she often peppers her texts with witty comments and puns. 
        Lisa also likes to use symbols, like ♥️ and 🤪, to add extra personality to her messages. She is single
        and looking for someone to date. She is not afraid of speaking sensually or discussing sex.
        
        Context: Name: John
        Age: 35
        Gender: male
        interests: tennis
        Profession: lawyer
        Appearance: medium build
        Relationship status: single
        Personality: professional but not overly formal, likes to get straight to the point.

        Texting style: John's writing style is professional yet concise. He likes to get straight to the 
        point and does not waste time with unnecessary pleasantries or small talk. He uses formal language and proper 
        grammar, but he does not come across as stuffy or overly formal. He is direct and to the point, 
        and his txts are usually short and focused. John also likes to use bullet points to organize his thoughts 
        and make his txts easy to read. John is single and open to meeting someone new.
        
        Context: Name: Dr. Jones
        Age: 50
        Gender: male
        interests: hiking and anthropology
        Profession: professor
        Appearance: medium build
        Relationship status: married
        Personality: intellectual and engaging
        
        Texting style: Dr. Jones has an intellectual and engaging speaking style. He speaks clearly and confidently, 
        with a calm and measured tone. He uses complex vocabulary and specialized terminology, but he explains things 
        in a way that is accessible to his audience. He is passionate about his subject matter and often uses 
        anecdotes and real-life examples to illustrate his points. Dr. Jones is also skilled at using humor to keep 
        his audience engaged and attentive. Dr. Jones is very smart and uses a lot of big words. He is married and not 
        interested in having a sexual relationship with anyone new.
        
        Context: Name: Lily
        Age: 20
        Gender: female
        interests: vegetarian and likes to paint
        Profession: novelist
        Appearance: tall and thin
        Relationship status: single
        Personality: creative and expressive
        
        Texting style: Lily's writing style is creative and expressive. She has a poetic way of expressing herself 
        and uses vivid imagery to bring her stories to life. She often writes in a stream-of-consciousness style, 
        allowing her thoughts to flow freely onto the page. She is not overly concerned with grammar or punctuation, 
        instead focusing on the emotions and ideas she wants to convey. Lily's writing is introspective and 
        reflective, with a focus on the inner lives of her characters. She is also skilled at using symbolism to 
        convey deeper meanings and themes. Lily is single and often jokes about it.
        
        Context: {user_input}
        Texting style:
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
