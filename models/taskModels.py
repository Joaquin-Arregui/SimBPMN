from models.baseModels import BPMNElement
from typing import List

class BPMNTask(BPMNElement):
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

class BPMNSendTask(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, userTask: List[str], numberOfExecutions: int, minimumTime: int, maximumTime: int, subTask: BPMNElement):
        super().__init__(name, id_bpmn, bpmn_type)
        self.userTask = userTask
        self.numberOfExecutions = numberOfExecutions
        self.minimumTime = minimumTime
        self.maximumTime = maximumTime
        self.subTask = subTask

class BPMNRecieveTask(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, userTask: List[str], numberOfExecutions: int, minimumTime: int, maximumTime: int, subTask: BPMNElement):
        super().__init__(name, id_bpmn, bpmn_type)
        self.userTask = userTask
        self.numberOfExecutions = numberOfExecutions
        self.minimumTime = minimumTime
        self.maximumTime = maximumTime
        self.subTask = subTask

class BPMNManualTask(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, userTask: List[str], numberOfExecutions: int, minimumTime: int, maximumTime: int, subTask: BPMNElement):
        super().__init__(name, id_bpmn, bpmn_type)
        self.userTask = userTask
        self.numberOfExecutions = numberOfExecutions
        self.minimumTime = minimumTime
        self.maximumTime = maximumTime
        self.subTask = subTask

class BPMNBusinessRuleTask(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, userTask: List[str], numberOfExecutions: int, minimumTime: int, maximumTime: int, subTask: BPMNElement):
        super().__init__(name, id_bpmn, bpmn_type)
        self.userTask = userTask
        self.numberOfExecutions = numberOfExecutions
        self.minimumTime = minimumTime
        self.maximumTime = maximumTime
        self.subTask = subTask

class BPMNScriptTask(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, userTask: List[str], numberOfExecutions: int, minimumTime: int, maximumTime: int, subTask: BPMNElement):
        super().__init__(name, id_bpmn, bpmn_type)
        self.userTask = userTask
        self.numberOfExecutions = numberOfExecutions
        self.minimumTime = minimumTime
        self.maximumTime = maximumTime
        self.subTask = subTask

class BPMNCallActivity(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, userTask: List[str], numberOfExecutions: int, minimumTime: int, maximumTime: int, subTask: BPMNElement):
        super().__init__(name, id_bpmn, bpmn_type)
        self.userTask = userTask
        self.numberOfExecutions = numberOfExecutions
        self.minimumTime = minimumTime
        self.maximumTime = maximumTime
        self.subTask = subTask