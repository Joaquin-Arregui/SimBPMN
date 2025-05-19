import os
from chatbot.gpt4o import gptCall
from chatbot.llama import llamaCall
from chatbot.deepseek import deepseekCall

def callAPI(chat, llm):
    if llm == "gpt":
        answer = gptCall(chat)
    elif llm == "llama":
        answer = llamaCall(chat)
    elif llm == "deepseek":
        answer = deepseekCall(chat)
    else: 
        return "Selected an invalid LLM"

    return answer