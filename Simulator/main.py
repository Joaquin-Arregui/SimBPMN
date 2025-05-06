import subprocess
import os
from generateScript import generateScript
from generateSecurityScript import generateScript as generateSecurityScript
from models.parser import parse_bpmn_elements

rulesPath = 'files/esperTasks.txt'

with open(rulesPath, 'r') as f:
    file_content = f.read()
elements, process, starts, messageStarts, trackSecurity = parse_bpmn_elements(file_content)
if elements[process].security:
    script, process = generateSecurityScript(elements, process, starts, messageStarts, trackSecurity)
else:
    script, process = generateScript(elements, process, starts, messageStarts, trackSecurity)
script_name = f'script_{process}.py'
with open(script_name, 'w') as f:
    f.write(script)

subprocess.run(['python', script_name])
os.remove(rulesPath)
os.remove(script_name)