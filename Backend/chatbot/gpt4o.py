import os
from dotenv import load_dotenv

load_dotenv()

def gptCall(chat):
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=chat,
            temperature=0.2,
            top_p=0.7,
            max_tokens=8192
        )
        return response.choices[0].message.content
    except Exception as e:
        print("Error calling OpenAI:", e)
        return str(e)