from heatMap.main import getHeatMap
from simulator.main import processSimulation
from chatbot.main import callAPI
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

MESSAGES = []

@app.route('/simulate', methods=['POST'])
def startSimulation():

    data = request.get_json(force=True)

    rules = data.get("content", "").strip()
    diagram = data.get("diagramXML", "").strip()

    scriptDir = os.path.dirname(__file__)
    resultsPath = os.path.join(os.path.dirname(scriptDir), 'Backend', 'heatMap', 'files', 'resultSimulation.xes')

    processSimulation(rules)

    with open(resultsPath, "r") as f:
        simulation = f.read()

    systemPrompt = """\
You are an assistant expert in BPMN modeling and simulation. The following logs and BPMN data describe a process with multiple lanes and user roles. Use them as context to answer questions or provide suggestions.
"""

    contextInfo = f"""
Simulation Log:
{simulation}

Diagram BPMN:
{diagram}
"""

    global MESSAGES
    MESSAGES = [
        {"role": "system", "content": systemPrompt},
        {"role": "system", "content": "Context:\n" + contextInfo},
    ]

    heatMap = getHeatMap(diagram)

    os.remove(resultsPath)
    return jsonify({"simulation": simulation, "heatMap": heatMap, "reply":"Type your message below."})

@app.route('/continueChat', methods=['POST'])
def continueChat():
    global MESSAGES

    data = request.get_json(force=True)

    user_message = data.get("message", "").strip()
    llm = data.get("llm", "").strip()

    if not user_message:
        return jsonify({"reply": "No message received."}), 400
    MESSAGES.append({"role": "user", "content": user_message})

    answer = callAPI(MESSAGES, llm)

    MESSAGES.append({"role": "assistant", "content": answer})
    return jsonify({"reply": answer})

if __name__ == '__main__':
    app.run(port=3000, debug=False)