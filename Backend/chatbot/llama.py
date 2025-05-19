import os
from dotenv import load_dotenv

load_dotenv()

def llamaCall(chat):
    import openai
    openai.base_url="https://integrate.api.nvidia.com/v1"
    openai.api_key=os.getenv("LLAMA_API_KEY")
    try:
        completion = openai.chat.completions.create(
            model="meta/llama-3.1-405b-instruct",
            messages=chat,
            temperature=0.2,
            top_p=0.7,
            max_tokens=8192
        )
        answer = ""
        answer = completion.choices[0].message.content
    except Exception as e:
        print("Error calling OpenAI:", e)
        answer = str(e)
    return answer