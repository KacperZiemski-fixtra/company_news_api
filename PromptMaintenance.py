import os
from dotenv import load_dotenv
from langfuse import Langfuse
from openai import OpenAI


def get_prompt(prompt_name):
    load_dotenv()

    try:
        langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST")
        )

        langfuse.auth_check()

        prompt = langfuse.get_prompt(prompt_name)

        return prompt
    except Exception as e:
        print(e)

def query_openai_responses_web_search(prompt, text_format):
    try:
        load_dotenv()
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.responses.parse(
            model="gpt-4o-mini",
            tools=[{"type": "web_search_preview"}],
            store=False,
            input=prompt,
            text_format=text_format
        )

        return response
    except Exception as e:
        print(e)
        return []

# def query_openai_responses(prompt, text_format):
#     try:
#         load_dotenv()
#         client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#
#         response = client.responses.parse(
#             model="gpt-4o-mini",
#             store=False,
#             input=prompt,
#             text_format=text_format
#         )
#
#         return response
#     except Exception as e:
#         print(e)
#         return []