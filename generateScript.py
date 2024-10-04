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
        f.write('''\n''' + name + ': [type={element.bpmn_type}, name={element.name}, id_bpmn={element.name}, subTask="' + selectedElement + '", startTime=' + str(env.now) + ']')
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
    with open('results/results_{next(iter(elements))}.txt', 'a') as f:
        f.write('''\n''' + name + ': [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, userTask="jl", numberOfExecutions={element.numberOfExecutions}, time=' + str(random.randint({element.minimumTime}, {element.maximumTime})) + ', subTask="{element.subTask}", startTime=' + str(env.now) + ']')
    yield env.timeout(random.randint({element.minimumTime}, {element.maximumTime}))
    return '{element.subTask}'
    """
    return generateFunction(elements, element.subTask, script + functionStr)

def serviceTask(elements, element, script):
    return script

def manualTask(elements, element, script):
    functionStr = f"""
def {element.id_bpmn}(env, name):
    with open('results/results_{next(iter(elements))}.txt', 'a') as f:
        f.write('''\n''' + name + ': [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, userTask="jl", numberOfExecutions={element.numberOfExecutions}, time=' + str(random.randint({element.minimumTime}, {element.maximumTime})) + ', subTask="{element.subTask}", startTime=' + str(env.now) + ']')
    yield env.timeout(random.randint({element.minimumTime}, {element.maximumTime}))
    return '{element.subTask}'
    """
    return generateFunction(elements, element.subTask, script + functionStr)

def userTask(elements, element, script):
    functionStr = f"""
def {element.id_bpmn}(env, name):
    with open('results/results_{next(iter(elements))}.txt', 'a') as f:
        f.write('''\n''' + name + ': [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, userTask="jl", numberOfExecutions={element.numberOfExecutions}, time=' + str(random.randint({element.minimumTime}, {element.maximumTime})) + ', subTask="{element.subTask}", startTime=' + str(env.now) + ']')
    yield env.timeout(random.randint({element.minimumTime}, {element.maximumTime}))
    return '{element.subTask}'
    """
    return generateFunction(elements, element.subTask, script + functionStr)

def parallelGateway(elements, element, script):
    possibleElements, _ = getPercentOfBranches(elements, element.id_bpmn)
    functionStr = f"""
def {element.id_bpmn}(env, name):
    strSelectedElements = ""
    for element in {possibleElements}:
        if element == '{possibleElements[-1]}':
            strSelectedElements = strSelectedElements + element
        else:
            strSelectedElements = strSelectedElements + element + ', '
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
    selectedElements = [element for element, percent in zip({possibleElements}, {percents}) if random.random() < percent]
    strSelectedElements = ""
    for element in selectedElements:
        if element == selectedElements[-1]:
            strSelectedElements = strSelectedElements + element
        else:
            strSelectedElements = strSelectedElements + element + ', '
    with open('results/results_Process_1.txt', 'a') as f:
        f.write('''
''' + name + ': Element: [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, subTask="' + strSelectedElements + '", startTime=' + str(env.now) + ']')
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
        return parallelGateway(elements, element, script)
    elif elementType == "BPMNTask":
        return task(elements, element, script)
    elif elementType == "BPMNServiceTask":
        return serviceTask(elements, element, script)
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
    scriptMainFunction = f"""
def start_process(env, name):
    nextTask = ['{startEvent.subTask}']
    while nextTask:
        tasks = []
        for task in nextTask:
            tasks.append(globals()[task])
        nextTask = []
        processes = []
        results = []
        for task in tasks:
            process = env.process(task(env, name))
            processes.append(process)
            results.append(process)
        yield simpy.events.AllOf(env, processes)
        for result in results:
            if result.value:
                if isinstance(result.value, list):
                    nextTask.extend(result.value)
                else:
                    nextTask.append(result.value)


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
"""
    return script + scriptMainFunction, process