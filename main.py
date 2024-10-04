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
    print(name + ': Selected task ' + selectedElement)
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
    print(name + ': Executing task {element.id_bpmn} at ' + str(env.now))
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
            print(name + ': Ended the process at ' + str(env.now))
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
    script = """
import simpy
import random

"""
    script = script + "nInstances=" + str(elements[process].instances) + "\n"
    script = script + "frequency=" + str(elements[process].frequency) + "\n"
    startEvent = elements[start]
    script = generateFunction(elements, startEvent.subTask, script)
    scriptMainFunction = f"""
def start_process(env, name):
    nextTask = '{startEvent.subTask}'
    while(nextTask!=''):"""
    scriptMainFunction = generateMainFunction(elements, startEvent.subTask, scriptMainFunction)
    script = script + scriptMainFunction + """
def main(env):
    for i in range (nInstances):
        env.process(start_process(env, f'Instance {i+1}'))
        yield env.timeout(frequency)

env = simpy.Environment()
env.process(main(env))
env.run()
"""
    return script

file_content = """
### Esper Rules Export ###

Element: [type=bpmn:Process, name=Unnamed, id_bpmn=Process_1, instances=20, frequency=40]
Element: [type=bpmn:StartEvent, name=Unnamed, id_bpmn=StartEvent_0offpno, subTask="Gateway_0qga3of"]
Element: [type=bpmn:ExclusiveGateway, name=Unnamed, id_bpmn=Gateway_0qga3of, subTask="Activity_1r1vk2z, Activity_0d5rvvx"]
Element: [type=bpmn:SequenceFlow, name=Unnamed, id_bpmn=Flow_0pqjhmz, superElement="StartEvent_0offpno", subElement="Gateway_0qga3of"]
Element: [type=bpmn:Task, name=Unnamed, id_bpmn=Activity_1r1vk2z, userTask="jl, alba", numberOfExecutions=2, minimumTime=20, maximumTime=40, subTask="Activity_1mrbi73"]
Element: [type=bpmn:SequenceFlow, name=Unnamed, id_bpmn=Flow_1uxvcj5, percentageOfBranches=70, superElement="Gateway_0qga3of", subElement="Activity_1r1vk2z"]
Element: [type=bpmn:Task, name=Unnamed, id_bpmn=Activity_1mrbi73, userTask="jl,alba", numberOfExecutions=2, minimumTime=10, maximumTime=30, subTask="Event_1qr2r1y"]
Element: [type=bpmn:SequenceFlow, name=Unnamed, id_bpmn=Flow_1t97n81, superElement="Activity_1r1vk2z", subElement="Activity_1mrbi73"]
Element: [type=bpmn:Task, name=Unnamed, id_bpmn=Activity_0d5rvvx, userTask="alba", numberOfExecutions=2, minimumTime=10, maximumTime=20, subTask="Event_0pfkrjg"]
Element: [type=bpmn:SequenceFlow, name=Unnamed, id_bpmn=Flow_168m8d9, percentageOfBranches=30, superElement="Gateway_0qga3of", subElement="Activity_0d5rvvx"]
Element: [type=bpmn:EndEvent, name=Unnamed, id_bpmn=Event_0pfkrjg, subTask=""]
Element: [type=bpmn:SequenceFlow, name=Unnamed, id_bpmn=Flow_00rvuul, superElement="Activity_0d5rvvx", subElement="Event_0pfkrjg"]
Element: [type=bpmn:EndEvent, name=Unnamed, id_bpmn=Event_1qr2r1y, subTask=""]
Element: [type=bpmn:SequenceFlow, name=Unnamed, id_bpmn=Flow_1hq8etr, superElement="Activity_1mrbi73", subElement="Event_1qr2r1y"]"""

script = generateScript(file_content)
with open('script.py', 'x') as f:
    f.write(script)
