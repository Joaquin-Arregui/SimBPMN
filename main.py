import subprocess
import os
from generateScript import generateScript

rulesPath = 'files/esperTasks.txt'

with open(rulesPath, 'r') as f:
    file_content = f.read()

script, process = generateScript(file_content)
script_name = f'script_{process}.py'
with open(script_name, 'x') as f:
    f.write(script)

subprocess.run(['python', script_name])
os.remove(rulesPath)
os.remove(script_name)
