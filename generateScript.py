from models import parse_bpmn_elements

def getPercentOfBranches(elements, gateway):
    possibleElements = []
    percents = []
    for element in elements.values():
        if type(element).__name__ == "BPMNSequenceFlow" and element.superElement == gateway:
            possibleElements.append(element.subElement)
            percents.append(element.percentageOfBranches / 100)
    return possibleElements, percents

def exclusiveGateway(elements, element, script):
    possibleElements, percents = getPercentOfBranches(elements, element.id_bpmn)
    functionStr = f"""
def {element.id_bpmn}(env, name):
    selectedElement = random.choices({possibleElements}, {percents})[0]
    with open('results/results_{next(iter(elements))}.txt', 'a') as f:
        f.write('''\n''' + name + ': [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, subTask="' + selectedElement + '", startTime=' + str(env.now) + ']')
    yield env.timeout(0)
    return selectedElement
    """
    extendedScript = script + functionStr
    for element in possibleElements:
        if element not in script:
            extendedScript = generateFunction(elements, element, extendedScript)
    return extendedScript

def task(elements, element, script):
    functionStr = f"""
def {element.id_bpmn}(env, name):
    time = 0
    for n in range({element.numberOfExecutions}):
        time += random.randint({element.minimumTime}, {element.maximumTime})
    with open('results/results_{next(iter(elements))}.txt', 'a') as f:
        f.write('''\n''' + name + ': [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, userTask="jl", numberOfExecutions={element.numberOfExecutions}, time=' + str(time) + ', subTask="{element.subTask}", startTime=' + str(env.now) + ']')
    yield env.timeout(time)
    return '{element.subTask}'
    """
    return generateFunction(elements, element.subTask, script + functionStr)


def manualTask(elements, element, script):
    functionStr = f"""
def {element.id_bpmn}(env, name):
    time = 0
    for _ in range({element.numberOfExecutions}):
        time += random.randint({element.minimumTime}, {element.maximumTime})
    with open('results/results_{next(iter(elements))}.txt', 'a') as f:
        f.write('''\n''' + name + ': [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, userTask="jl", numberOfExecutions={element.numberOfExecutions}, time=' + str(time) + ', subTask="{element.subTask}", startTime=' + str(env.now) + ']')
    yield env.timeout(time)
    return '{element.subTask}'
    """
    return generateFunction(elements, element.subTask, script + functionStr)


def userTask(elements, element, script):
    functionStr = f"""
def {element.id_bpmn}(env, name):
    time = 0
    for n in range({element.numberOfExecutions}):
        time += random.randint({element.minimumTime}, {element.maximumTime})
    with open('results/results_{next(iter(elements))}.txt', 'a') as f:
        f.write('''\n''' + name + ': [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, userTask="jl", numberOfExecutions={element.numberOfExecutions}, time=' + str(time) + ', subTask="{element.subTask}", startTime=' + str(env.now) + ']')
    yield env.timeout(time)
    return '{element.subTask}'
    """
    return generateFunction(elements, element.subTask, script + functionStr)


def parallelGateway(elements, element, script):
    possibleElements, _ = getPercentOfBranches(elements, element.id_bpmn)
    functionStr = f"""
def {element.id_bpmn}(env, name):
    strSelectedElements = ", ".join({possibleElements})
    with open('results/results_{next(iter(elements))}.txt', 'a') as f:
        f.write('''\n''' + name + ': [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, subTask="' + strSelectedElements + '", startTime=' + str(env.now) + ']')
    yield env.timeout(0)
    return {possibleElements}
    """
    extendedScript = script + functionStr
    for element in possibleElements:
        if element not in script:
            extendedScript = generateFunction(elements, element, extendedScript)
    return extendedScript


def inclusiveGateway(elements, element, script):
    possibleElements, percents = getPercentOfBranches(elements, element.id_bpmn)
    functionStr = f"""
def {element.id_bpmn}(env, name):
    elements = {possibleElements}
    percents = {percents}
    selectedElements = [element for element, percent in zip(elements, percents) if random.random() < percent]
    if not selectedElements:
        selectedElements = random.choices(elements, weights=percents, k=1)
    strSelectedElements = ", ".join(selectedElements)
    with open('results/results_Process_1.txt', 'a') as f:
        f.write('''
''' + name + ': [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, subTask="' + strSelectedElements + '", startTime=' + str(env.now) + ']')
    yield env.timeout(0)
    return selectedElements
    """
    extendedScript = script + functionStr
    for element in possibleElements:
        if element not in script:
            extendedScript = generateFunction(elements, element, extendedScript)
    return extendedScript


def endEvent(elements, element, script):
    functionStr = f"""
def {element.id_bpmn}(env, name):
    with open('results/results_{next(iter(elements))}.txt', 'a') as f:
        f.write('''\n''' + name + ': [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, subTask="", startTime=' + str(env.now) + ']')
    yield env.timeout(0)
    """
    return script + functionStr


def generateFunction(elements, elementId, script):
    element = elements[elementId]
    elementType = type(element).__name__
    if elementType == "BPMNExclusiveGateway":
        return exclusiveGateway(elements, element, script)
    elif elementType == "BPMNTask":
        return task(elements, element, script)
    elif elementType == "BPMNManualTask":
        return manualTask(elements, element, script)
    elif elementType == "BPMNUserTask":
        return userTask(elements, element, script)
    elif elementType == "BPMNParallelGateway":
        return parallelGateway(elements, element, script)
    elif elementType == "BPMNInclusiveGateway":
        return inclusiveGateway(elements, element, script)
    elif elementType == "BPMNEndEvent":
        return endEvent(elements, element, script)


def serviceTask(elements):
    script = f"""
def checkServiceTasks(name):
    with open('results/results_{next(iter(elements))}.txt', 'r') as f:
        content = f.readlines()"""
    for element in elements.values():
        if element.bpmn_type == 'bpmn:ServiceTask':
            script = script + """
    found1=False
    activities = {"""
            subTasks = element.subTask
            for subElement in subTasks:
                if subElement != subTasks[-1]:
                    script = script + f'''
        '{subElement}': False,'''
                else:
                    script = script + f'''
        '{subElement}': False'''
            script = script + '''
    }''' + f'''
    last_activity_index = -1
    line_index = -1
    for line in content:
        line_index += 1
        if name in line and 'id_bpmn={element.id_bpmn}' in line:
            found1 = True''' + '''
        for activity in activities:
            if name in line and f'id_bpmn={activity}' in line:
                activities[activity] = True
                last_activity_index = line_index'''
            n = 1 if element.uocSecurity else 2
            script = script + f"""
    number_found = sum(activities.values())
    if not found1 and number_found >= {n} and last_activity_index != -1:
        subtasks_str = ", ".join([activity for activity, found in activities.items() if found])
        new_line = name + ': [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, sodSecurity={element.sodSecurity}, bodSecurity={element.bodSecurity}, uocSecurity={element.uocSecurity}, nu={element.nu}, mth={element.mth}, subTask="' + subtasks_str + '''"]
'''
        content.insert(last_activity_index+1, new_line)"""
    return script + """
    with open('results/results_Process_1.txt', 'w') as f:
        f.writelines(content)
"""


def generateScript(content):
    elements, process, start = parse_bpmn_elements(content)
    elementProcess = elements[process]
    script = """
import simpy
import random

"""
    script = script + "nInstances=" + str(elementProcess.instances) + "\n"
    script = script + "frequency=" + str(elementProcess.frequency) + "\n"
    startEvent = elements[start]
    script = generateFunction(elements, startEvent.subTask, script)
    scriptServiceTask = serviceTask(elements)
    scriptMainFunction = f"""
def process_task(env, name, task_name):
    task_func = globals()[task_name]
    result = yield env.process(task_func(env, name))
    if result:
        if isinstance(result, list):
            for next_task in result:
                env.process(process_task(env, name, next_task))
        else:
            env.process(process_task(env, name, result))

def start_process(env, name):
    yield env.process(process_task(env, name, '{startEvent.subTask}'))

def main(env):
    with open('results/results_"""+ next(iter(elements)) + """.txt', 'a') as f:
            f.write("Element: [type=""" + f'{elementProcess.bpmn_type}, name={elementProcess.name}, id_bpmn={elementProcess.id_bpmn}, instances={elementProcess.instances}, frequency={elementProcess.frequency}]")'  + """
    for i in range (nInstances):
        with open('results/results_"""+ next(iter(elements)) + """.txt', 'a') as f:
            f.write(f'''\nInstance {i+1}: [type=""" + startEvent.bpmn_type + ', name=' + startEvent.name + ', id_bpmn=' + startEvent.id_bpmn + ', subTask="'+ startEvent.subTask + """", startTime=''' + str(env.now) + ']')
        env.process(start_process(env, f'Instance {i+1}'))
        yield env.timeout(frequency)

env = simpy.Environment()
env.process(main(env))
env.run()
for i in range(nInstances):
    checkServiceTasks(f'Instance {i+1}')
"""
    return script + scriptServiceTask + scriptMainFunction, process