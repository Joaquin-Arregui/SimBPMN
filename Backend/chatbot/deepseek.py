import os
from dotenv import load_dotenv

load_dotenv()

def deepseekCall(chat):
    import openai
    openai.api_key=os.getenv("DEEPSEEK_API_KEY")
    try:
        completion = openai.chat.completions.create(
            model="deepseek-chat",
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