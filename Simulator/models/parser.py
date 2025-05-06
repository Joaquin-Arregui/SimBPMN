import ast
import re
from models.baseModels import BPMNProcess, BPMNCollaboration, BPMNParticipant, BPMNLane, BPMNSequenceFlow, BPMNDataInputAssociation, BPMNDataOutputAssociation, BPMNMessageFlow, BPMNServiceTask, BPMNDataObjectReference
from models.startEventModels import BPMNStartEvent, BPMNMessageStartEvent
from models.gatewayModels import BPMNExclusiveGateway, BPMNInclusiveGateway, BPMNParallelGateway, BPMNEventBasedGateway
from models.taskModels import BPMNTask, BPMNUserTask, BPMNSendTask, BPMNReceiveTask, BPMNManualTask, BPMNBusinessRuleTask, BPMNScriptTask, BPMNCallActivity
from models.endEventModels import BPMNEndEvent
from models.intermediateEventModels import BPMNIntermediateThrowEvent, BPMNMessageIntermediateCatchEvent, BPMNMessageIntermediateThrowEvent, BPMNTimerIntermediateCatchEvent
from models.subprocessModels import BPMNSubProcess, BPMNTransaction

def parse_bpmn_elements(file_content: str):
    users =  {}
    elements = {}
    securityTasks = {}
    start = []
    messageStart = []
    messageFlows = []
    messageThrowElement = []
    messageCatchElement = []
    trackSecurity = False
    dataOutPuts = []
    dataInPuts = []
    requiredData = {}
    generatedData = {}
    defaultData = []
    dataInfo = {}
    participants = []
    elementsContainedParticipants = {}
    lanes = []
    elementsContainedLanes = {}
    elementsContainer = {}
    startsParticipant = {}
    connections = {}
    element_pattern = re.compile(r'Element: \[type=(?P<type>[a-zA-Z:]+), name="(?P<name>[^"]+)", id_bpmn=(?P<id_bpmn>[^,]+)(?:, (.*))?\]')

    for line in file_content.splitlines():
        match = element_pattern.match(line)
        if match and not (match.group("type").split(":")[-1] == "Association" or match.group("type").split(":")[-1] == "TextAnnotation"):
            element_type = match.group("type").split(":")[-1]
            name = match.group("name").strip('"')
            id_bpmn = match.group("id_bpmn").strip('"')
            bpmn_type = match.group("type")
            if element_type == "Process":
                process = id_bpmn
                instances = int(re.search(r'instances=(\d+)', line).group(1))
                frequency = int(re.search(r'frequency=(\d+)', line).group(1))
                userWithoutRole_match = re.search(r'userWithoutRole=(\[[^\]]*\])', line)
                if userWithoutRole_match:
                    userWithoutRole_str = userWithoutRole_match.group(1)
                    userWithoutRole = ast.literal_eval(userWithoutRole_str)
                else:
                    userWithoutRole = []
                userWithRole_match = re.search(r'userWithRole=({[^}]+})', line)
                if userWithRole_match:
                    userWithRole_str = userWithRole_match.group(1)
                    userWithRole = ast.literal_eval(userWithRole_str)
                else:
                    userWithRole = {}
                if re.search(r'security=(\w+)', line):
                    security = re.search(r'security=(\w+)', line).group(1) == "true"
                else:
                    security = False
                element = BPMNProcess(name, id_bpmn, bpmn_type, instances, frequency, userWithoutRole, userWithRole, security)

            elif element_type == "Collaboration":
                process = id_bpmn
                instances = int(re.search(r'instances=(\d+)', line).group(1))
                security = re.search(r'security=(\w+)', line).group(1) == "true"
                element = BPMNCollaboration(name, id_bpmn, bpmn_type, instances, security)

            elif element_type == "Participant":
                users_match = re.search(r'userWithoutRole=(\[[^\]]*\])', line)
                if users_match:
                    users_str = users_match.group(1)
                    participant_users = ast.literal_eval(users_str)
                else:
                    participant_users = []
                frequency = int(re.search(r'frequency=(\d+)', line).group(1))
                contained_elements_str = re.search(r'containedElements=\[([^\]]*)\]', line).group(1)
                contained_elements = [element.strip('"') for element in contained_elements_str.split(", ")]
                element = BPMNParticipant(name, id_bpmn, bpmn_type, frequency, participant_users, contained_elements)
                users[id_bpmn] = participant_users
                participants.append([frequency, id_bpmn])
                elementsContainedParticipants[id_bpmn] = contained_elements

            elif element_type == "Lane":
                users_match = re.search(r'userWithoutRole=(\[[^\]]*\])', line)
                if users_match:
                    users_str = users_match.group(1)
                    lane_users = ast.literal_eval(users_str)
                else:
                    lane_users = []
                contained_elements_str = re.search(r'containedElements=\[([^\]]*)\]', line).group(1)
                contained_elements = [element.strip('"') for element in contained_elements_str.split(", ")]
                users[id_bpmn] = lane_users
                element = BPMNLane(name, id_bpmn, bpmn_type, lane_users, contained_elements)
                elementsContainedLanes[id_bpmn] = contained_elements
                lanes.append(id_bpmn)

            elif element_type == "SequenceFlow":
                superElement = re.search(r'superElement="([^"]+)"', line).group(1)
                subElement = re.search(r'subElement="([^"]+)"', line).group(1)
                percentage = re.search(r'percentageOfBranches=(\d+)', line)
                percentage = float(percentage.group(1)) if percentage else None
                if subElement in connections.keys():
                    connections[subElement].append(superElement)
                else:
                    connections[subElement] = [superElement]
                element = BPMNSequenceFlow(name, id_bpmn, bpmn_type, superElement, subElement, percentage)

            elif element_type == "DataOutputAssociation":
                superElement = re.search(r'superElement="([^"]+)"', line).group(1)
                subElement = re.search(r'subElement="([^"]+)"', line).group(1)
                element = BPMNDataOutputAssociation(name, id_bpmn, bpmn_type, superElement, subElement)
                dataOutPuts.append(element)

            elif element_type == "DataInputAssociation":
                superElement = re.search(r'superElement="([^"]+)"', line).group(1)
                subElement = re.search(r'subElement="([^"]+)"', line).group(1)
                element = BPMNDataInputAssociation(name, id_bpmn, bpmn_type, superElement, subElement)
                dataInPuts.append(element)

            elif element_type == "MessageFlow":
                superElement = re.search(r'superElement="([^"]+)"', line).group(1)
                subElement = re.search(r'subElement="([^"]+)"', line).group(1)
                element = BPMNMessageFlow(name, id_bpmn, bpmn_type, superElement, subElement)
                messageFlows.append(element)

            elif element_type == "StartEvent":
                start.append(id_bpmn)
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNStartEvent(name, id_bpmn, bpmn_type, subTask)

            elif element_type == "MessageStartEvent":
                messageStart.append(id_bpmn)
                messageCatchElement.append(id_bpmn)
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNMessageStartEvent(name, id_bpmn, bpmn_type, None, subTask)

            elif element_type == "ExclusiveGateway":
                subTask = re.search(r'subTask="([^"]+)"', line).group(1).split(', ')
                element = BPMNExclusiveGateway(name, id_bpmn, bpmn_type, subTask)

            elif element_type == "ParallelGateway":
                subTask = re.search(r'subTask="([^"]+)"', line).group(1).split(', ')
                element = BPMNParallelGateway(name, id_bpmn, bpmn_type, subTask)

            elif element_type == "InclusiveGateway":
                subTask = re.search(r'subTask="([^"]+)"', line).group(1).split(', ')
                element = BPMNInclusiveGateway(name, id_bpmn, bpmn_type, subTask)

            elif element_type == "EventBasedGateway":
                subTask = re.search(r'subTask="([^"]+)"', line).group(1).split(', ')
                element = BPMNEventBasedGateway(name, id_bpmn, bpmn_type, subTask)

            elif element_type == "Task":
                userTask = match.group(1).split(', ') if (match := re.search(r'userTask="([^"]+)"', line)) else None
                numberOfExecutions = int(re.search(r'numberOfExecutions=(\d+)', line).group(1))
                minimumTime = int(re.search(r'minimumTime=(\d+)', line).group(1))
                maximumTime = int(re.search(r'maximumTime=(\d+)', line).group(1))
                loopParameter_match = re.search(r'loopParameter=({[^}]+})', line)
                if loopParameter_match:
                    loopParameter_str = loopParameter_match.group(1)
                    loopParameter = ast.literal_eval(loopParameter_str)
                else:
                    loopParameter = None
                multiInstanceType_match = re.search(r'multiInstanceType="([^"]+)"', line)
                if multiInstanceType_match:
                    multiInstanceType_str = multiInstanceType_match.group(1)
                    multiInstanceType = multiInstanceType_str == "true"
                else:
                    multiInstanceType = None
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNTask(name, id_bpmn, bpmn_type, userTask, numberOfExecutions, minimumTime, maximumTime, loopParameter, multiInstanceType, subTask)
            
            elif element_type == "UserTask":
                userTask = match.group(1).split(', ') if (match := re.search(r'userTask="([^"]+)"', line)) else None
                numberOfExecutions = int(re.search(r'numberOfExecutions=(\d+)', line).group(1))
                minimumTime = int(re.search(r'minimumTime=(\d+)', line).group(1))
                maximumTime = int(re.search(r'maximumTime=(\d+)', line).group(1))
                loopParameter_match = re.search(r'loopParameter=({[^}]+})', line)
                if loopParameter_match:
                    loopParameter_str = loopParameter_match.group(1)
                    loopParameter = ast.literal_eval(loopParameter_str)
                else:
                    loopParameter = None
                multiInstanceType_match = re.search(r'multiInstanceType="([^"]+)"', line)
                if multiInstanceType_match:
                    multiInstanceType_str = multiInstanceType_match.group(1)
                    multiInstanceType = multiInstanceType_str == "true"
                else:
                    multiInstanceType = None
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNUserTask(name, id_bpmn, bpmn_type, userTask, numberOfExecutions, minimumTime, maximumTime, loopParameter, multiInstanceType, subTask)

            elif element_type == "SendTask":
                messageThrowElement.append(id_bpmn)
                userTask = match.group(1).split(', ') if (match := re.search(r'userTask="([^"]+)"', line)) else None
                numberOfExecutions = int(re.search(r'numberOfExecutions=(\d+)', line).group(1))
                minimumTime = int(re.search(r'minimumTime=(\d+)', line).group(1))
                maximumTime = int(re.search(r'maximumTime=(\d+)', line).group(1))
                messageDestiny = None
                loopParameter_match = re.search(r'loopParameter=({[^}]+})', line)
                if loopParameter_match:
                    loopParameter_str = loopParameter_match.group(1)
                    loopParameter = ast.literal_eval(loopParameter_str)
                else:
                    loopParameter = None
                multiInstanceType_match = re.search(r'multiInstanceType="([^"]+)"', line)
                if multiInstanceType_match:
                    multiInstanceType_str = multiInstanceType_match.group(1)
                    multiInstanceType = multiInstanceType_str == "true"
                else:
                    multiInstanceType = None
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNSendTask(name, id_bpmn, bpmn_type, userTask, numberOfExecutions, minimumTime, maximumTime, messageDestiny, loopParameter, multiInstanceType, subTask)

            elif element_type == "ReceiveTask":
                messageCatchElement.append(id_bpmn)
                userTask = match.group(1).split(', ') if (match := re.search(r'userTask="([^"]+)"', line)) else None
                numberOfExecutions = int(re.search(r'numberOfExecutions=(\d+)', line).group(1))
                minimumTime = int(re.search(r'minimumTime=(\d+)', line).group(1))
                maximumTime = int(re.search(r'maximumTime=(\d+)', line).group(1))
                messageOrigin = None
                loopParameter_match = re.search(r'loopParameter=({[^}]+})', line)
                if loopParameter_match:
                    loopParameter_str = loopParameter_match.group(1)
                    loopParameter = ast.literal_eval(loopParameter_str)
                else:
                    loopParameter = None
                multiInstanceType_match = re.search(r'multiInstanceType="([^"]+)"', line)
                if multiInstanceType_match:
                    multiInstanceType_str = multiInstanceType_match.group(1)
                    multiInstanceType = multiInstanceType_str == "true"
                else:
                    multiInstanceType = None
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNReceiveTask(name, id_bpmn, bpmn_type, userTask, numberOfExecutions, minimumTime, maximumTime, messageOrigin, loopParameter, multiInstanceType, subTask)
            
            elif element_type == "ManualTask":
                userTask = match.group(1).split(', ') if (match := re.search(r'userTask="([^"]+)"', line)) else None
                numberOfExecutions = int(re.search(r'numberOfExecutions=(\d+)', line).group(1))
                minimumTime = int(re.search(r'minimumTime=(\d+)', line).group(1))
                maximumTime = int(re.search(r'maximumTime=(\d+)', line).group(1))
                loopParameter_match = re.search(r'loopParameter=({[^}]+})', line)
                if loopParameter_match:
                    loopParameter_str = loopParameter_match.group(1)
                    loopParameter = ast.literal_eval(loopParameter_str)
                else:
                    loopParameter = None
                multiInstanceType_match = re.search(r'multiInstanceType="([^"]+)"', line)
                if multiInstanceType_match:
                    multiInstanceType_str = multiInstanceType_match.group(1)
                    multiInstanceType = multiInstanceType_str == "true"
                else:
                    multiInstanceType = None
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNManualTask(name, id_bpmn, bpmn_type, userTask, numberOfExecutions, minimumTime, maximumTime, loopParameter, multiInstanceType, subTask)

            elif element_type == "BusinessRuleTask":
                userTask = match.group(1).split(', ') if (match := re.search(r'userTask="([^"]+)"', line)) else None
                numberOfExecutions = int(re.search(r'numberOfExecutions=(\d+)', line).group(1))
                minimumTime = int(re.search(r'minimumTime=(\d+)', line).group(1))
                maximumTime = int(re.search(r'maximumTime=(\d+)', line).group(1))
                loopParameter_match = re.search(r'loopParameter=({[^}]+})', line)
                if loopParameter_match:
                    loopParameter_str = loopParameter_match.group(1)
                    loopParameter = ast.literal_eval(loopParameter_str)
                else:
                    loopParameter = None
                multiInstanceType_match = re.search(r'multiInstanceType="([^"]+)"', line)
                if multiInstanceType_match:
                    multiInstanceType_str = multiInstanceType_match.group(1)
                    multiInstanceType = multiInstanceType_str == "true"
                else:
                    multiInstanceType = None
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNBusinessRuleTask(name, id_bpmn, bpmn_type, userTask, numberOfExecutions, minimumTime, maximumTime, loopParameter, multiInstanceType, subTask)

            elif element_type == "ScriptTask":
                userTask = match.group(1).split(', ') if (match := re.search(r'userTask="([^"]+)"', line)) else None
                numberOfExecutions = int(re.search(r'numberOfExecutions=(\d+)', line).group(1))
                minimumTime = int(re.search(r'minimumTime=(\d+)', line).group(1))
                maximumTime = int(re.search(r'maximumTime=(\d+)', line).group(1))
                loopParameter_match = re.search(r'loopParameter=({[^}]+})', line)
                if loopParameter_match:
                    loopParameter_str = loopParameter_match.group(1)
                    loopParameter = ast.literal_eval(loopParameter_str)
                else:
                    loopParameter = None
                multiInstanceType_match = re.search(r'multiInstanceType="([^"]+)"', line)
                if multiInstanceType_match:
                    multiInstanceType_str = multiInstanceType_match.group(1)
                    multiInstanceType = multiInstanceType_str == "true"
                else:
                    multiInstanceType = None
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNScriptTask(name, id_bpmn, bpmn_type, userTask, numberOfExecutions, minimumTime, maximumTime, loopParameter, multiInstanceType, subTask)
            
            elif element_type == "CallActivity":
                userTask = match.group(1).split(', ') if (match := re.search(r'userTask="([^"]+)"', line)) else None
                numberOfExecutions = int(re.search(r'numberOfExecutions=(\d+)', line).group(1))
                minimumTime = int(re.search(r'minimumTime=(\d+)', line).group(1))
                maximumTime = int(re.search(r'maximumTime=(\d+)', line).group(1))
                loopParameter_match = re.search(r'loopParameter=({[^}]+})', line)
                if loopParameter_match:
                    loopParameter_str = loopParameter_match.group(1)
                    loopParameter = ast.literal_eval(loopParameter_str)
                else:
                    loopParameter = None
                multiInstanceType_match = re.search(r'multiInstanceType="([^"]+)"', line)
                if multiInstanceType_match:
                    multiInstanceType_str = multiInstanceType_match.group(1)
                    multiInstanceType = multiInstanceType_str == "true"
                else:
                    multiInstanceType = None
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNCallActivity(name, id_bpmn, bpmn_type, userTask, numberOfExecutions, minimumTime, maximumTime, loopParameter, multiInstanceType, subTask)

            elif element_type == "ServiceTask":
                trackSecurity = True
                sodSecurity = re.search(r'sodSecurity=(\w+)', line).group(1) == "true"
                bodSecurity = re.search(r'bodSecurity=(\w+)', line).group(1) == "true"
                uocSecurity = re.search(r'uocSecurity=(\w+)', line).group(1) == "true"
                if re.search(r'mth=(\d+)', line):
                    mth = int(re.search(r'mth=(\d+)', line).group(1))
                else:
                    mth = 0
                subTask = re.search(r'subTask="([^"]+)"', line).group(1).split(', ')
                element = BPMNServiceTask(name, id_bpmn, bpmn_type, sodSecurity, bodSecurity, uocSecurity, mth, subTask)
                for task in subTask:
                    if task in securityTasks.keys():
                        securityTasks[task][id_bpmn] = [sodSecurity, bodSecurity, uocSecurity, mth]
                    else:
                        securityTasks[task] = {id_bpmn: [sodSecurity, bodSecurity, uocSecurity, mth]}

            elif element_type == "IntermediateThrowEvent":
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNIntermediateThrowEvent(name, id_bpmn, bpmn_type, subTask)

            elif element_type == "MessageIntermediateCatchEvent":
                messageCatchElement.append(id_bpmn)
                messageOrigin = None
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNMessageIntermediateCatchEvent(name, id_bpmn, bpmn_type, messageOrigin, subTask)

            elif element_type == "MessageIntermediateThrowEvent":
                messageThrowElement.append(id_bpmn)
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                messageDestiny = None
                element = BPMNMessageIntermediateThrowEvent(name, id_bpmn, bpmn_type, messageDestiny, subTask)

            elif element_type == "TimerIntermediateCatchEvent":
                time = int(re.search(r'time=(\d+)', line).group(1)) 
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNTimerIntermediateCatchEvent(name, id_bpmn, bpmn_type, time, subTask)

            elif element_type == "SubProcess":
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNSubProcess(name, id_bpmn, bpmn_type, subTask)

            elif element_type == "Transaction":
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNTransaction(name, id_bpmn, bpmn_type, subTask)

            elif element_type == "EndEvent":
                subTask = re.search(r'subTask="([^"]*)"', line).group(1) or None
                element = BPMNEndEvent(name, id_bpmn, bpmn_type, subTask)

            elif element_type == "DataObjectReference":
                element = BPMNDataObjectReference(name, id_bpmn, bpmn_type)
                dataInfo[id_bpmn] = name
            elements[element.id_bpmn] = element

    for dataInPut in dataInPuts:
        if dataInPut.subElement in requiredData.keys():
            requiredData[dataInPut.subElement].append(dataInPut.superElement)
        else:
            requiredData[dataInPut.subElement] = [dataInPut.superElement]
    for dataOutPut in dataOutPuts:
        if dataOutPut.subElement in generatedData.keys():
            generatedData[dataOutPut.superElement].append(dataOutPut.subElement)
        else:
            generatedData[dataOutPut.superElement] = [dataOutPut.subElement]
    for data in requiredData.values():
        if data not in generatedData.values():
            defaultData.extend(data)
    for messageFlow in messageFlows:
        originId = messageFlow.superElement
        destinyId = messageFlow.subElement
        origin = elements[originId]
        destiny = elements[destinyId]
        origin.messageDestiny = destinyId
        destiny.messageOrigin = originId
        elements[originId] = origin
        elements[destinyId] = destiny

    for lane, containedElement in elementsContainedLanes.items():
        for e in containedElement:
            elementsContainer[e] = lane
    for participant, containedElement in elementsContainedParticipants.items():
        for e in containedElement:
            if not e in elementsContainer.keys():
                elementsContainer[e] = participant
            if e in start or e in messageStart:
                startsParticipant[e] = participant
    gatewayConnections = {}
    for destiny, origins in connections.items():
        if (elements[destiny].bpmn_type == 'bpmn:ParallelGateway' or elements[destiny].bpmn_type == 'bpmn:InclusiveGateway') and len(origins) > 1:
            gatewayConnections[destiny] = origins

    elements['lanes'] = lanes
    elements['users'] = users
    elements['security'] = securityTasks
    elements['generatedData'] = generatedData
    elements['requiredData'] = requiredData
    elements['defaultData'] = defaultData
    elements['dataInfo'] = dataInfo
    elements['participants'] = participants
    elements['elementsContainer'] = elementsContainer
    elements['startsParticipant'] = startsParticipant
    elements['gatewayConnections'] = gatewayConnections

    return elements, process, start, messageStart, trackSecurity
