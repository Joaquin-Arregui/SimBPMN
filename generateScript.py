from models import parse_bpmn_elements

def getPercentOfBranches(elements, gateway):
    possibleElements = []
    percents = []
    for element in elements.values():
        if type(element).__name__ == "BPMNSequenceFlow" and element.superElement == gateway:
            possibleElements.append(element.subElement)
            percents.append(element.percentageOfBranches/100)
    return possibleElements, percents


def exclusiveGateway(elements, element, script):
    possibleElements, percents = getPercentOfBranches(elements, element.id_bpmn)
    functionStr = f"""
def {element.id_bpmn}(env, name):
    selectedElement = random.choices({possibleElements}, {percents})[0]
    with open('results/results_{next(iter(elements))}.txt', 'a') as f:
        f.write('''\n''' + name + ': Element: [type={element.bpmn_type}, name={element.name}, id_bpmn={element.name}, subTask="' + selectedElement + '"]')
    return selectedElement
    """
    extendedScript = script+functionStr
    for element in possibleElements:
        if element not in script:
            extendedScript = generateFunction(elements, element, extendedScript)
    return extendedScript


def task(elements, element, script):
    functionStr = f"""
def {element.id_bpmn}(env, name):
    with open('results/results_{next(iter(elements))}.txt', 'a') as f:
        f.write('''\n''' + name + ': Element: [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, userTask="jl", numberOfExecutions={element.numberOfExecutions}, time='+str(random.randint({element.minimumTime}, {element.maximumTime}))+', subTask="{element.subTask}"]')
    yield env.timeout(random.randint({element.minimumTime}, {element.maximumTime}))
    """
    return generateFunction(elements, element.subTask, script+functionStr)


def serviceTask(elements, element, script):
    return 0


def generateFunction(elements, elementId, script):
    element = elements[elementId]
    elementType = type(element).__name__
    if elementType == "BPMNExclusiveGateway":
        return exclusiveGateway(elements, element, script)
    elif elementType == "BPMNTask":
        return task(elements, element, script)
    elif elementType == "BPMNServiceTask":
        return serviceTask(elements, element, script)
    elif elementType == "BPMNEndEvent":
        return script


def mainExclusiveGateway(elements, element, script):
    script = script + f"""
        if nextTask == '{element.id_bpmn}':
            nextTask = {element.id_bpmn}(env, name)"""
    possibleElements, _ = getPercentOfBranches(elements, element.id_bpmn)
    for element in possibleElements:
        if element not in script:
            script = generateMainFunction(elements, element, script)
    return script


def mainTask(elements, element, script):
    script = script + f"""
        if nextTask == '{element.id_bpmn}':
            yield env.process({element.id_bpmn}(env, name))
            nextTask = '{element.subTask}'"""
    if f'def element.subTask' not in script:
        script = generateMainFunction(elements, element.subTask, script)
    return script


def mainServiceTask(elements, element, script):
    return script


def mainEndEvent(elements, element, script):
    script = script + f"""
        if nextTask == '{element.id_bpmn}':
            with open('results/results_{next(iter(elements))}.txt', 'a') as f:
                f.write('''\n''' + name + ': Element: [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, subTask=""]')
            nextTask = ''"""
    return script


def generateMainFunction(elements, elementId, script):
    element = elements[elementId]
    elementType = type(element).__name__
    if elementType == "BPMNExclusiveGateway":
        return mainExclusiveGateway(elements, element, script)
    elif elementType == "BPMNTask":
        return mainTask(elements, element, script)
    elif elementType == "BPMNServiceTask":
        return mainServiceTask(elements, element, script)
    elif elementType == "BPMNEndEvent":
        return mainEndEvent(elements, element, script)

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
    nextTask = '{startEvent.subTask}'
    while(nextTask!=''):"""
    scriptMainFunction = generateMainFunction(elements, startEvent.subTask, scriptMainFunction)
    script = script + scriptMainFunction + """
def main(env):
    with open('results/results_"""+ next(iter(elements)) + """.txt', 'a') as f:
            f.write("Element: [type=""" + f'{elementProcess.bpmn_type}, name={elementProcess.name}, id_bpmn={elementProcess.id_bpmn}, instances={elementProcess.instances}, frequency={elementProcess.frequency}]")'  + """
    for i in range (nInstances):
        with open('results/results_"""+ next(iter(elements)) + """.txt', 'a') as f:
            f.write(f'''\nInstance {i+1}: Element: [type=""" + startEvent.bpmn_type + ', name=' + startEvent.name + ', id_bpmn=' + startEvent.id_bpmn + ', subTask="'+ startEvent.subTask + """"]''')
        env.process(start_process(env, f'Instance {i+1}'))
        yield env.timeout(frequency)

env = simpy.Environment()
env.process(main(env))
env.run()
"""
    return script, process
