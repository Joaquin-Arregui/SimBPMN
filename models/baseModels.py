from typing import List, Dict

class BPMNElement:
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str):
        self.name = name
        self.id_bpmn = id_bpmn
        self.bpmn_type = bpmn_type

class BPMNProcess(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, instances: int, frequency: int, userWithoutRole: List[str], userWithRole: Dict[str, List[str]]):
        super().__init__(name, id_bpmn, bpmn_type)
        self.instances = instances
        self.frequency = frequency
        self.userWithoutRole = userWithoutRole
        self.userWithRole = userWithRole

class BPMNSequenceFlow(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, superElement: BPMNElement, subElement: BPMNElement, percentageOfBranches: float = None):
        super().__init__(name, id_bpmn, bpmn_type)
        self.superElement = superElement
        self.subElement = subElement
        self.percentageOfBranches = percentageOfBranches

class BPMNServiceTask(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, sodSecurity: bool, bodSecurity: bool, uocSecurity: bool, nu: int, mth: int, subTask: List[BPMNElement]):
        super().__init__(name, id_bpmn, bpmn_type)
        self.sodSecurity = sodSecurity
        self.bodSecurity = bodSecurity
        self.uocSecurity = uocSecurity
        self.nu = nu
        self.mth = mth
        self.subTask = subTask