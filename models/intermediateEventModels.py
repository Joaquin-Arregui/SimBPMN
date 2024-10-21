from models.baseModels import BPMNElement

class BPMNIntermediateThrowEvent(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: BPMNElement):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask

class BPMNMessageIntermediateCatchEvent(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: BPMNElement):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask

class BPMNMessageIntermediateThrowEvent(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: BPMNElement):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask

class BPMNTimerIntermediateCatchEvent(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: BPMNElement):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask

class BPMNEscalationIntermediateThrowEvent(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: BPMNElement):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask

class BPMNConditionalIntermediateCatchEvent(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: BPMNElement):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask

class BPMNLinkIntermediateCatchEvent(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: BPMNElement):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask

class BPMNLinkIntermediateThrowEvent(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: BPMNElement):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask

class BPMNCompensationIntermediateThrowEven(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: BPMNElement):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask

class BPMNSignalIntermediateCatchEvent(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: BPMNElement):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask

class BPMNSignalIntermediateThrowEvent(BPMNElement):
    def __init__(self, name: str, id_bpmn: str, bpmn_type: str, subTask: BPMNElement):
        super().__init__(name, id_bpmn, bpmn_type)
        self.subTask = subTask