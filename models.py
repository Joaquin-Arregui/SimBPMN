import re
from typing import List, Union

class BPMNElement:
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str):
        self.name = name
        self.id_bpmn = id_bpmn
        self.bpmn_type = bpmn_type

class BPMNProcess(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, instances: int, frequency: int):
        super().__init__(name, id_bpmn, bpmn_type)
        self.instances = instances
        self.frequency = frequency

class BPMNStartEvent(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: BPMNElement):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask

class BPMNExclusiveGateway(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: List[BPMNElement]):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask

class BPMNSequenceFlow(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, superElement: BPMNElement, subElement: BPMNElement, percentageOfBranches: float = None):
        super().__init__(name, id_bpmn, bpmn_type)
        self.superElement = superElement
        self.subElement = subElement
        self.percentageOfBranches = percentageOfBranches

class BPMNTask(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, userTask: List[str], numberOfExecutions: int, minimumTime: int, maximumTime: int, subTask: BPMNElement):
        super().__init__(name, id_bpmn, bpmn_type)
        self.userTask = userTask
        self.numberOfExecutions = numberOfExecutions
        self.minimumTime = minimumTime
        self.maximumTime = maximumTime
        self.subTask = subTask

class BPMNServiceTask(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, sodSecurity: bool, bodSecurity: bool, uocSecurity: bool, nu: int, mth: int, subTask: List[BPMNElement]):
        super().__init__(name, id_bpmn, bpmn_type)
        self.sodSecurity = sodSecurity
        self.bodSecurity = bodSecurity
        self.uocSecurity = uocSecurity
        self.nu = nu
        self.mth = mth
        self.subTask = subTask

class BPMNEndEvent(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: Union[BPMNElement, None]):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask

class BPMNManualTask(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, userTask: List[str], numberOfExecutions: int, minimumTime: int, maximumTime: int, subTask: BPMNElement):
        super().__init__(name, id_bpmn, bpmn_type)
        self.userTask = userTask
        self.numberOfExecutions = numberOfExecutions
        self.minimumTime = minimumTime
        self.maximumTime = maximumTime
        self.subTask = subTask

class BPMNUserTask(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, userTask: List[str], numberOfExecutions: int, minimumTime: int, maximumTime: int, subTask: BPMNElement):
        super().__init__(name, id_bpmn, bpmn_type)
        self.userTask = userTask
        self.numberOfExecutions = numberOfExecutions
        self.minimumTime = minimumTime
        self.maximumTime = maximumTime
        self.subTask = subTask

class BPMNParallelGateway(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: List[BPMNElement]):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask

class BPMNInclusiveGateway(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: List[BPMNElement]):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask

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
                element = BPMNProcess(name, id_bpmn, bpmn_type, instances, frequency)

            elif element_type == "StartEvent":
                start = id_bpmn
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNStartEvent(name, id_bpmn, bpmn_type, subTask)

            elif element_type == "ExclusiveGateway":
                subTask = re.search(r'subTask="([^"]+)"', line).group(1).split(', ')
                element = BPMNExclusiveGateway(name, id_bpmn, bpmn_type, subTask)

            elif element_type == "SequenceFlow":
                superElement = re.search(r'superElement="([^"]+)"', line).group(1)
                subElement = re.search(r'subElement="([^"]+)"', line).group(1)
                percentage = re.search(r'percentageOfBranches=(\d+)', line)
                percentage = float(percentage.group(1)) if percentage else None
                element = BPMNSequenceFlow(name, id_bpmn, bpmn_type, superElement, subElement, percentage)

            elif element_type == "Task":
                userTask = re.search(r'userTask="([^"]+)"', line).group(1).split(', ')
                numberOfExecutions = int(re.search(r'numberOfExecutions=(\d+)', line).group(1))
                minimumTime = int(re.search(r'minimumTime=(\d+)', line).group(1))
                maximumTime = int(re.search(r'maximumTime=(\d+)', line).group(1))
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNTask(name, id_bpmn, bpmn_type, userTask, numberOfExecutions, minimumTime, maximumTime, subTask)

            elif element_type == "ServiceTask":
                sodSecurity = re.search(r'sodSecurity=(\w+)', line).group(1) == "true"
                bodSecurity = re.search(r'bodSecurity=(\w+)', line).group(1) == "true"
                uocSecurity = re.search(r'uocSecurity=(\w+)', line).group(1) == "true"
                nu = int(re.search(r'nu=(\d+)', line).group(1))
                mth = int(re.search(r'mth=(\d+)', line).group(1))
                subTask = re.search(r'subTask="([^"]+)"', line).group(1).split(', ')
                element = BPMNServiceTask(name, id_bpmn, bpmn_type, sodSecurity, bodSecurity, uocSecurity, nu, mth, subTask)

            elif element_type == "EndEvent":
                subTask = re.search(r'subTask="([^"]*)"', line).group(1) or None
                element = BPMNEndEvent(name, id_bpmn, bpmn_type, subTask)

            elif element_type == "ManualTask":
                userTask = re.search(r'userTask="([^"]+)"', line).group(1).split(', ')
                numberOfExecutions = int(re.search(r'numberOfExecutions=(\d+)', line).group(1))
                minimumTime = int(re.search(r'minimumTime=(\d+)', line).group(1))
                maximumTime = int(re.search(r'maximumTime=(\d+)', line).group(1))
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNTask(name, id_bpmn, bpmn_type, userTask, numberOfExecutions, minimumTime, maximumTime, subTask)
            
            elif element_type == "UserTask":
                userTask = re.search(r'userTask="([^"]+)"', line).group(1).split(', ')
                numberOfExecutions = int(re.search(r'numberOfExecutions=(\d+)', line).group(1))
                minimumTime = int(re.search(r'minimumTime=(\d+)', line).group(1))
                maximumTime = int(re.search(r'maximumTime=(\d+)', line).group(1))
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNTask(name, id_bpmn, bpmn_type, userTask, numberOfExecutions, minimumTime, maximumTime, subTask)

            elif element_type == "ParallelGateway":
                subTask = re.search(r'subTask="([^"]+)"', line).group(1).split(', ')
                element = BPMNParallelGateway(name, id_bpmn, bpmn_type, subTask)

            elif element_type == "InclusiveGateway":
                subTask = re.search(r'subTask="([^"]+)"', line).group(1).split(', ')
                element = BPMNInclusiveGateway(name, id_bpmn, bpmn_type, subTask)

            elements[element.id_bpmn] = element

    return elements, process, start
