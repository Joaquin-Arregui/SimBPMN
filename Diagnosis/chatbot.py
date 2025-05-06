# chatbot.py
import os
from dotenv import load_dotenv
import openai 
from flask import Flask, request, jsonify
from flask_cors import CORS

# Load environment variables (OPENAI_API_KEY, etc.)
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)
# Paths to your files (modify as needed)
simulationPath = r"../Simulator/files/resultSimulation.xes"
violationPath = r"../Modeler/example/src/files/violations.txt"
diagramPath    = r"../Simulator/files/diagram.bpmn"

# Read file contents for context
try:
    with open(simulationPath, "r", encoding="utf-8") as f:
        simulationContent = f.read()
except:
    simulationContent = ""

try:
    with open(violationPath, "r", encoding="utf-8") as f:
        violationContent = f.read()
except:
    violationContent = ""

try:
    with open(diagramPath, "r", encoding="utf-8") as f:
        diagramContent = f.read()
except:
    diagramContent = ""

SYSTEM_PROMPT = """\
You are an assistant expert in BPMN modeling, simulation, and security. The following logs and BPMN data describe a process with multiple lanes and user roles, including violation data. Use them as context to answer questions or provide suggestions.
"""

CONTEXT_INFO = f"""
Violation Instances:
{violationContent}

Simulation Log:
{simulationContent}

Diagram BPMN:
{diagramContent}
"""
MESSAGES = []

@app.route('/newChat', methods=['POST'])
def startChat():
    global MESSAGES
    MESSAGES = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": "Context:\n" + CONTEXT_INFO},
    ]
    return jsonify({"reply": "Type your message below."})

@app.route('/continueChat', methods=['POST'])
def continueChat():
    global MESSAGES
    print(MESSAGES)
    data = request.get_json(force=True)
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "No message received."}), 400
    MESSAGES.append({"role": "user", "content": user_message})
    try:
        completion = openai.chat.completions.create(
            model="gpt-4o",
            messages=MESSAGES,
            temperature=0.2,
            top_p=0.7,
            max_tokens=8192
        )
        answer = ""
        answer = completion.choices[0].message.content
        MESSAGES.append({"role": "assistant", "content": answer})
        print("New message processed: " + user_message)
    except Exception as e:
        print("Error calling OpenAI:", e)
        answer = str(e)
    return jsonify({"reply": answer})

if __name__ == '__main__':
    app.run(port=3001, debug=False)
