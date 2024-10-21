import ast
import re
from models.baseModels import BPMNProcess, BPMNSequenceFlow, BPMNServiceTask
from models.startEventModels import BPMNStartEvent
from models.gatewayModels import BPMNExclusiveGateway, BPMNInclusiveGateway, BPMNParallelGateway, BPMNEventBasedGateway
from models.taskModels import BPMNTask, BPMNUserTask, BPMNSendTask, BPMNRecieveTask, BPMNManualTask, BPMNBusinessRuleTask, BPMNScriptTask, BPMNCallActivity
from models.endEventModels import BPMNEndEvent
from models.intermediateEventModels import BPMNIntermediateThrowEvent, BPMNMessageIntermediateCatchEvent, BPMNMessageIntermediateThrowEvent, BPMNTimerIntermediateCatchEvent
from models.subprocessModels import BPMNSubProcess, BPMNTransaction

def parse_bpmn_elements(file_content: str):
    elements = {}
    element_pattern = re.compile(r'Element: \[type=(?P<type>[a-zA-Z:]+), name=(?P<name>[^,]+), id_bpmn=(?P<id_bpmn>[^,]+)(?:, (.*))?\]')

    for line in file_content.splitlines():
        match = element_pattern.match(line)

        if match:
            element_type = match.group("type").split(":")[-1]
            name = match.group("name").strip('"')
            id_bpmn = match.group("id_bpmn")
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

                element = BPMNProcess(name, id_bpmn, bpmn_type, instances, frequency, userWithoutRole, userWithRole)

            elif element_type == "SequenceFlow":
                superElement = re.search(r'superElement="([^"]+)"', line).group(1)
                subElement = re.search(r'subElement="([^"]+)"', line).group(1)
                percentage = re.search(r'percentageOfBranches=(\d+)', line)
                percentage = float(percentage.group(1)) if percentage else None
                element = BPMNSequenceFlow(name, id_bpmn, bpmn_type, superElement, subElement, percentage)

            elif element_type == "StartEvent":
                start = id_bpmn
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNStartEvent(name, id_bpmn, bpmn_type, subTask)

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
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNTask(name, id_bpmn, bpmn_type, userTask, numberOfExecutions, minimumTime, maximumTime, subTask)
            
            elif element_type == "UserTask":
                userTask = match.group(1).split(', ') if (match := re.search(r'userTask="([^"]+)"', line)) else None
                numberOfExecutions = int(re.search(r'numberOfExecutions=(\d+)', line).group(1))
                minimumTime = int(re.search(r'minimumTime=(\d+)', line).group(1))
                maximumTime = int(re.search(r'maximumTime=(\d+)', line).group(1))
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNUserTask(name, id_bpmn, bpmn_type, userTask, numberOfExecutions, minimumTime, maximumTime, subTask)

            elif element_type == "SendTask":
                userTask = match.group(1).split(', ') if (match := re.search(r'userTask="([^"]+)"', line)) else None
                numberOfExecutions = int(re.search(r'numberOfExecutions=(\d+)', line).group(1))
                minimumTime = int(re.search(r'minimumTime=(\d+)', line).group(1))
                maximumTime = int(re.search(r'maximumTime=(\d+)', line).group(1))
                messageDestiny = re.search(r'messageDestiny=([^\s,]+)', line).group(1)
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNSendTask(name, id_bpmn, bpmn_type, userTask, numberOfExecutions, minimumTime, maximumTime, messageDestiny, subTask)

            elif element_type == "RecieveTask":
                userTask = match.group(1).split(', ') if (match := re.search(r'userTask="([^"]+)"', line)) else None
                numberOfExecutions = int(re.search(r'numberOfExecutions=(\d+)', line).group(1))
                minimumTime = int(re.search(r'minimumTime=(\d+)', line).group(1))
                maximumTime = int(re.search(r'maximumTime=(\d+)', line).group(1))
                messageOrigin = re.search(r'messageOrigin=([^\s,]+)', line).group(1)
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNRecieveTask(name, id_bpmn, bpmn_type, userTask, numberOfExecutions, minimumTime, maximumTime, messageOrigin, subTask)
            
            elif element_type == "ManualTask":
                userTask = match.group(1).split(', ') if (match := re.search(r'userTask="([^"]+)"', line)) else None
                numberOfExecutions = int(re.search(r'numberOfExecutions=(\d+)', line).group(1))
                minimumTime = int(re.search(r'minimumTime=(\d+)', line).group(1))
                maximumTime = int(re.search(r'maximumTime=(\d+)', line).group(1))
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNManualTask(name, id_bpmn, bpmn_type, userTask, numberOfExecutions, minimumTime, maximumTime, subTask)

            elif element_type == "BusinessRuleTask":
                userTask = match.group(1).split(', ') if (match := re.search(r'userTask="([^"]+)"', line)) else None
                numberOfExecutions = int(re.search(r'numberOfExecutions=(\d+)', line).group(1))
                minimumTime = int(re.search(r'minimumTime=(\d+)', line).group(1))
                maximumTime = int(re.search(r'maximumTime=(\d+)', line).group(1))
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNBusinessRuleTask(name, id_bpmn, bpmn_type, userTask, numberOfExecutions, minimumTime, maximumTime, subTask)

            elif element_type == "ScriptTask":
                userTask = match.group(1).split(', ') if (match := re.search(r'userTask="([^"]+)"', line)) else None
                numberOfExecutions = int(re.search(r'numberOfExecutions=(\d+)', line).group(1))
                minimumTime = int(re.search(r'minimumTime=(\d+)', line).group(1))
                maximumTime = int(re.search(r'maximumTime=(\d+)', line).group(1))
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNScriptTask(name, id_bpmn, bpmn_type, userTask, numberOfExecutions, minimumTime, maximumTime, subTask)
            
            elif element_type == "CallActivity":
                userTask = match.group(1).split(', ') if (match := re.search(r'userTask="([^"]+)"', line)) else None
                numberOfExecutions = int(re.search(r'numberOfExecutions=(\d+)', line).group(1))
                minimumTime = int(re.search(r'minimumTime=(\d+)', line).group(1))
                maximumTime = int(re.search(r'maximumTime=(\d+)', line).group(1))
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNCallActivity(name, id_bpmn, bpmn_type, userTask, numberOfExecutions, minimumTime, maximumTime, subTask)

            elif element_type == "ServiceTask":
                sodSecurity = re.search(r'sodSecurity=(\w+)', line).group(1) == "true"
                bodSecurity = re.search(r'bodSecurity=(\w+)', line).group(1) == "true"
                uocSecurity = re.search(r'uocSecurity=(\w+)', line).group(1) == "true"
                nu = int(re.search(r'nu=(\d+)', line).group(1))
                mth = int(re.search(r'mth=(\d+)', line).group(1))
                subTask = re.search(r'subTask="([^"]+)"', line).group(1).split(', ')
                element = BPMNServiceTask(name, id_bpmn, bpmn_type, sodSecurity, bodSecurity, uocSecurity, nu, mth, subTask)

            elif element_type == "IntermediateThrowEvent":
                start = id_bpmn
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNIntermediateThrowEvent(name, id_bpmn, bpmn_type, subTask)

            elif element_type == "MessageIntermediateCatchEvent":
                start = id_bpmn
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNMessageIntermediateCatchEvent(name, id_bpmn, bpmn_type, subTask)

            elif element_type == "MessageIntermediateThrowEvent":
                start = id_bpmn
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNMessageIntermediateThrowEvent(name, id_bpmn, bpmn_type, subTask)

            elif element_type == "TimerIntermediateCatchEvent":
                start = id_bpmn
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNTimerIntermediateCatchEvent(name, id_bpmn, bpmn_type, subTask)

            elif element_type == "SubProcess":
                start = id_bpmn
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNSubProcess(name, id_bpmn, bpmn_type, subTask)

            elif element_type == "Transaction":
                start = id_bpmn
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNTransaction(name, id_bpmn, bpmn_type, subTask)

            elif element_type == "EndEvent":
                subTask = re.search(r'subTask="([^"]*)"', line).group(1) or None
                element = BPMNEndEvent(name, id_bpmn, bpmn_type, subTask)

            elements[element.id_bpmn] = element

    return elements, process, start
