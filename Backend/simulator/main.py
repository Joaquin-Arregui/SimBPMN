import subprocess
import os
from simulator.generateScript import generateScript
from simulator.models.parser import parse_bpmn_elements

def processSimulation(rules):

    elements, process, starts, messageStarts = parse_bpmn_elements(rules)
    script, process = generateScript(elements, process, starts, messageStarts)
    script_name = f'script_{process}.py'
    with open(script_name, 'w') as f:
        f.write(script)

    subprocess.run(['python', script_name])
    os.remove(script_name)