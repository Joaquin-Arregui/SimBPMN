from models.baseModels import BPMNElement
from typing import Union

class BPMNEndEvent(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: Union[BPMNElement, None]):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask

class BPMNMessageEndEvent(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: Union[BPMNElement, None]):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask

class BPMNEscalationEndEvent(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: Union[BPMNElement, None]):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask

class BPMNErrorEndEvent(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: Union[BPMNElement, None]):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask

class BPMNCompensationEndEvent(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: Union[BPMNElement, None]):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask

class BPMNSignalEndEvent(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: Union[BPMNElement, None]):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask

class BPMNTerminateEndEvent(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: Union[BPMNElement, None]):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask