import subprocess
import os
from generateScript import generateScript
from generateSecurityScript import generateScript as generateSecurityScript
from models.parser import parse_bpmn_elements
from heatMap.generateHeatMap import getHeatMap

scriptDir = os.path.dirname(__file__)
rulesPath = os.path.join(os.path.dirname(scriptDir), 'Simulator', 'files', 'esperTasks.txt')

with open(rulesPath, 'r') as f:
    file_content = f.read()
elements, process, starts, messageStarts, trackSecurity = parse_bpmn_elements(file_content)
if elements[process].security:
    script, process = generateSecurityScript(elements, process, starts, messageStarts, trackSecurity)
else:
    script, process = generateScript(elements, process, starts, messageStarts, trackSecurity)
scriptName = f'script_{process}.py'
with open(scriptName, 'w') as f:
    f.write(script)

subprocess.run(['python', scriptName])


resultsPath = os.path.join(os.path.dirname(scriptDir), 'Simulator', 'files', 'resultSimulation.xes')

getHeatMap()
os.remove(rulesPath)
os.remove(scriptName)
os.remove(resultsPath)

