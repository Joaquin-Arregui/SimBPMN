import re
from typing import List, Union

class BPMNElement:
    def __init__(self, name: str, id_bpmn: str):
        self.name = name
        self.id_bpmn = id_bpmn

class BPMNProcess(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, instances: int, frequency: int):
        super().__init__(name, id_bpmn)
        self.instances = instances
        self.frequency = frequency

class BPMNStartEvent(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, subTask: BPMNElement):
        super().__init__(name, id_bpmn)
        self.subTask = subTask

class BPMNExclusiveGateway(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, subTask: List[BPMNElement]):
        super().__init__(name, id_bpmn)
        self.subTask = subTask

class BPMNSequenceFlow(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, superElement: BPMNElement, subElement: BPMNElement, percentageOfBranches: float = None):
        super().__init__(name, id_bpmn)
        self.superElement = superElement
        self.subElement = subElement
        self.percentageOfBranches = percentageOfBranches

class BPMNTask(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, userTask: List[str], numberOfExecutions: int, minimumTime: int, maximumTime: int, subTask: BPMNElement):
        super().__init__(name, id_bpmn)
        self.userTask = userTask
        self.numberOfExecutions = numberOfExecutions
        self.minimumTime = minimumTime
        self.maximumTime = maximumTime
        self.subTask = subTask

class BPMNServiceTask(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, sodSecurity: bool, bodSecurity: bool, uocSecurity: bool, nu: int, mth: int, subTask: List[BPMNElement]):
        super().__init__(name, id_bpmn)
        self.sodSecurity = sodSecurity
        self.bodSecurity = bodSecurity
        self.uocSecurity = uocSecurity
        self.nu = nu
        self.mth = mth
        self.subTask = subTask

class BPMNEndEvent(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, subTask: Union[BPMNElement, None]):
        super().__init__(name, id_bpmn)
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

            if element_type == "Process":
                process = id_bpmn
                instances = int(re.search(r'instances=(\d+)', line).group(1))
                frequency = int(re.search(r'frequency=(\d+)', line).group(1))
                element = BPMNProcess(name, id_bpmn, instances, frequency)

            elif element_type == "StartEvent":
                start = id_bpmn
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNStartEvent(name, id_bpmn, subTask)

            elif element_type == "ExclusiveGateway":
                subTask = re.search(r'subTask="([^"]+)"', line).group(1).split(', ')
                element = BPMNExclusiveGateway(name, id_bpmn, subTask)

            elif element_type == "SequenceFlow":
                superElement = re.search(r'superElement="([^"]+)"', line).group(1)
                subElement = re.search(r'subElement="([^"]+)"', line).group(1)
                percentage = re.search(r'percentageOfBranches=(\d+)', line)
                percentage = float(percentage.group(1)) if percentage else None
                element = BPMNSequenceFlow(name, id_bpmn, superElement, subElement, percentage)

            elif element_type == "Task":
                userTask = re.search(r'userTask="([^"]+)"', line).group(1).split(', ')
                numberOfExecutions = int(re.search(r'numberOfExecutions=(\d+)', line).group(1))
                minimumTime = int(re.search(r'minimumTime=(\d+)', line).group(1))
                maximumTime = int(re.search(r'maximumTime=(\d+)', line).group(1))
                subTask = re.search(r'subTask="([^"]+)"', line).group(1)
                element = BPMNTask(name, id_bpmn, userTask, numberOfExecutions, minimumTime, maximumTime, subTask)

            elif element_type == "ServiceTask":
                sodSecurity = re.search(r'sodSecurity=(\w+)', line).group(1) == "true"
                bodSecurity = re.search(r'bodSecurity=(\w+)', line).group(1) == "true"
                uocSecurity = re.search(r'uocSecurity=(\w+)', line).group(1) == "true"
                nu = int(re.search(r'nu=(\d+)', line).group(1))
                mth = int(re.search(r'mth=(\d+)', line).group(1))
                subTask = re.search(r'subTask="([^"]+)"', line).group(1).split(', ')
                element = BPMNServiceTask(name, id_bpmn, sodSecurity, bodSecurity, uocSecurity, nu, mth, subTask)

            elif element_type == "EndEvent":
                subTask = re.search(r'subTask="([^"]*)"', line).group(1) or None
                element = BPMNEndEvent(name, id_bpmn, subTask)
            
            elements[element.id_bpmn] = element

    return elements, process, start

# file_content = """
# ### Esper Rules Export ###

# Element: [type=bpmn:Process, name=Unnamed, id_bpmn=Process_1, instances=20, frequency=40]
# Element: [type=bpmn:StartEvent, name=Unnamed, id_bpmn=StartEvent_0offpno, subTask="Gateway_0qga3of"]
# Element: [type=bpmn:ExclusiveGateway, name=Unnamed, id_bpmn=Gateway_0qga3of, subTask="Activity_1r1vk2z, Activity_0d5rvvx"]
# Element: [type=bpmn:SequenceFlow, name=Unnamed, id_bpmn=Flow_0pqjhmz, superElement="StartEvent_0offpno", subElement="Gateway_0qga3of"]
# Element: [type=bpmn:Task, name=Unnamed, id_bpmn=Activity_1r1vk2z, userTask="jl, alba", numberOfExecutions=2, minimumTime=20, maximumTime=40, subTask="Activity_1mrbi73"]
# Element: [type=bpmn:SequenceFlow, name=Unnamed, id_bpmn=Flow_1uxvcj5, percentageOfBranches=70, superElement="Gateway_0qga3of", subElement="Activity_1r1vk2z"]
# Element: [type=bpmn:Task, name=Unnamed, id_bpmn=Activity_1mrbi73, userTask="jl,alba", numberOfExecutions=2, minimumTime=20, maximumTime=40, subTask="Event_1qr2r1y"]
# Element: [type=bpmn:SequenceFlow, name=Unnamed, id_bpmn=Flow_1t97n81, superElement="Activity_1r1vk2z", subElement="Activity_1mrbi73"]
# Element: [type=bpmn:Task, name=Unnamed, id_bpmn=Activity_0d5rvvx, userTask="alba", numberOfExecutions=2, minimumTime=20, maximumTime=40, subTask="Event_0pfkrjg"]
# Element: [type=bpmn:SequenceFlow, name=Unnamed, id_bpmn=Flow_168m8d9, percentageOfBranches=30, superElement="Gateway_0qga3of", subElement="Activity_0d5rvvx"]
# Element: [type=bpmn:EndEvent, name=Unnamed, id_bpmn=Event_0pfkrjg, subTask=""]
# Element: [type=bpmn:SequenceFlow, name=Unnamed, id_bpmn=Flow_00rvuul, superElement="Activity_0d5rvvx", subElement="Event_0pfkrjg"]
# Element: [type=bpmn:EndEvent, name=Unnamed, id_bpmn=Event_1qr2r1y, subTask=""]
# Element: [type=bpmn:SequenceFlow, name=Unnamed, id_bpmn=Flow_1hq8etr, superElement="Activity_1mrbi73", subElement="Event_1qr2r1y"]"""

# elements = parse_bpmn_elements(file_content)
# for elem in elements.keys():
#     element = elements[elem]
#     print(type(element).__name__ + " " + element.id_bpmn + ": " + str(vars(element)))
