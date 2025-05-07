from simulator.simulationFunctions.events import intermediateThrowEvent, messageIntermediateCatchEvent, messageIntermediateThrowEvent, timerIntermediateCatchEvent, endEvent
from simulator.simulationFunctions.gateways import exclusiveGateway, parallelGateway, inclusiveGateway
from simulator.simulationFunctions.generalTask import generalTask
from simulator.simulationFunctions.receiveTask import receiveTask
from simulator.simulationFunctions.sendTask import sendTask

GENERAL_TASKS = {
    "BPMNTask",
    "BPMNUserTask",
    "BPMNManualTask",
    "BPMNBusinessRuleTask",
    "BPMNScriptTask",
    "BPMNCallActivity",
    "BPMNServiceTask",
}

SPECIFIC_HANDLERS = {
    "BPMNExclusiveGateway":                 exclusiveGateway,
    "BPMNParallelGateway":                  parallelGateway,
    "BPMNInclusiveGateway":                 inclusiveGateway,
    "BPMNSendTask":                         sendTask,
    "BPMNReceiveTask":                      receiveTask,
    "BPMNIntermediateThrowEvent":           intermediateThrowEvent,
    "BPMNMessageIntermediateCatchEvent":    messageIntermediateCatchEvent,
    "BPMNMessageIntermediateThrowEvent":    messageIntermediateThrowEvent,
    "BPMNTimerIntermediateCatchEvent":      timerIntermediateCatchEvent,
    "BPMNEndEvent":                         endEvent,
}

def generateFunction(elements, element_id, script: bool = False):
    element = elements[element_id]
    element_type = type(element).__name__
    if element_type in GENERAL_TASKS:
        handler = generalTask
    else:
        handler = SPECIFIC_HANDLERS.get(element_type)
    return handler(elements, element, script)