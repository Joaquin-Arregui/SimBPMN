const axios = require('axios');

function getAllRelevantTasks(bpmnModeler) {
  var elementRegistry = bpmnModeler.get('elementRegistry');
  var definitions = bpmnModeler.get('canvas').getRootElement().businessObject.$parent;
  var id_model = definitions.diagrams[0].id;

  const elements = elementRegistry.filter((e) => true).map((e) => e.businessObject);
  const keyValuePairs = definitions.rootElements
    .filter((el) => el.$type === 'model:KeyValuePair')
    .map((pair) => ({
      key: pair.key,
      value: pair.value,
    }));

    elements.forEach((element) => {
      if (element.$type === 'bpmn:Process') {
        const businessObject = element;
        if (!businessObject.userWithRole) {
          businessObject.userWithRole = {};
        }
    
        keyValuePairs.forEach((pair) => {
          if (!businessObject.userWithRole[pair.key]) {
            businessObject.userWithRole[pair.key] = pair.value.split(',').map((v) => v.trim());
          }
        });
      }
    });    

  var relevantElements = elementRegistry.filter(e =>
    e.type === 'bpmn:Task' ||
    e.type === 'bpmn:ServiceTask' ||
    e.type === 'bpmn:UserTask' ||
    e.type === 'bpmn:ManualTask' ||
    e.type === 'bpmn:StartEvent' ||
    e.type === 'bpmn:EndEvent' ||
    e.type === 'bpmn:Process' ||
    e.type === 'bpmn:Collaboration' ||
    e.type === 'bpmn:Participant' ||
    e.type === 'bpmn:Lane' ||
    e.type === 'bpmn:SequenceFlow' ||
    e.type === 'bpmn:MessageFlow' ||
    e.type === 'bpmn:IntermediateCatchEvent' ||
    e.type === 'bpmn:DataObjectReference' ||
    e.type === 'bpmn:BoundaryEvent' ||
    e.type === 'bpmn:DataInputAssociation' ||
    e.type === 'bpmn:DataOutputAssociation' ||
    e.type.startsWith('bpmn:')
  );

  return relevantElements.map(e => {
    var businessObject = e.businessObject;

    let isMessageStartEvent = e.type === 'bpmn:StartEvent' && 
      businessObject.eventDefinitions && 
      businessObject.eventDefinitions.some(def => def.$type === 'bpmn:MessageEventDefinition');

    let isTimerStartEvent = e.type === 'bpmn:StartEvent' && 
      businessObject.eventDefinitions && 
      businessObject.eventDefinitions.some(def => def.$type === 'bpmn:TimerEventDefinition');

    let isMessageIntermediateCatchEvent = e.type === 'bpmn:IntermediateCatchEvent' && 
      businessObject.eventDefinitions && 
      businessObject.eventDefinitions.some(def => def.$type === 'bpmn:MessageEventDefinition');

    let isTimerIntermediateCatchEvent = e.type === 'bpmn:IntermediateCatchEvent' && 
      businessObject.eventDefinitions && 
      businessObject.eventDefinitions.some(def => def.$type === 'bpmn:TimerEventDefinition');

    let isMessageIntermediateThrowEvent = e.type === 'bpmn:IntermediateThrowEvent' && 
      businessObject.eventDefinitions && 
      businessObject.eventDefinitions.some(def => def.$type === 'bpmn:MessageEventDefinition');

    let type = e.type;
    if (isMessageStartEvent) {
      type = 'bpmn:MessageStartEvent';
    } else if (isTimerStartEvent) {
      type = 'bpmn:TimerStartEvent';
    } else if (isMessageIntermediateCatchEvent) {
      type = 'bpmn:MessageIntermediateCatchEvent';
    } else if (isTimerIntermediateCatchEvent) {
      type = 'bpmn:TimerIntermediateCatchEvent';
    } else if (isMessageIntermediateThrowEvent) {
      type = 'bpmn:MessageIntermediateThrowEvent';
    }

    var subTasks = [];
    var subElement = null;
    var superElement = null;

    if (e.type === 'bpmn:DataInputAssociation') {
      superElement = businessObject.sourceRef && businessObject.sourceRef.length > 0
          ? businessObject.sourceRef.map(source => source.id).join(', ')
          : 'No Super Element';
      const targetTask = elementRegistry.find(el =>
          el.businessObject.dataInputAssociations &&
          el.businessObject.dataInputAssociations.some(assoc => assoc.id === businessObject.id)
      );
      subElement = targetTask ? targetTask.businessObject.id : 'No Sub Element';
    } else if (e.type === 'bpmn:DataOutputAssociation') {
      subElement = businessObject.targetRef ? businessObject.targetRef.id : '';

      const parentTask = elementRegistry.find(el =>
          el.businessObject.dataOutputAssociations &&
          el.businessObject.dataOutputAssociations.some(assoc => assoc.id === businessObject.id)
      );
      superElement = parentTask ? [parentTask.businessObject.id].join(', ') : 'No Super Element';  
    } else if (e.type === 'bpmn:BoundaryEvent' && businessObject.attachedToRef) {
      const attachedTask = businessObject.attachedToRef;
      subElement = attachedTask.outgoing ? attachedTask.outgoing.map(flow => flow.targetRef.id).join(', ') : '';
      superElement = attachedTask.incoming ? attachedTask.incoming.map(flow => flow.sourceRef.id) : [];
    } else if (e.type === 'bpmn:SequenceFlow' || e.type === 'bpmn:MessageFlow') {
      subElement = businessObject.targetRef ? businessObject.targetRef.id : '';
      superElement = businessObject.sourceRef ? [businessObject.sourceRef.id] : [];
    } else {
      subTasks = businessObject.outgoing ? businessObject.outgoing.map(task => task.targetRef.id) : [];
      subElement = subTasks.join(', ');
      superElement = businessObject.incoming ? businessObject.incoming.map(flow => flow.sourceRef.id) : [];
    }

    const isServiceTask = e.type === 'bpmn:ServiceTask';
    const isUserTask = e.type === 'bpmn:UserTask';
    const isTask = e.type === 'bpmn:Task' || isUserTask;
    const isProcess = e.type === 'bpmn:Process';
    const isCollaboration = e.type === 'bpmn:Collaboration';
    const isParticipant = e.type === 'bpmn:Participant';
    const isLane = e.type === 'bpmn:Lane';
    const isSequenceFlow = e.type === 'bpmn:SequenceFlow' || e.type === 'bpmn:MessageFlow';
    const percentageOfBranches = isSequenceFlow ? (businessObject.percentageOfBranches || 0) : 0;

    let time = null;
    if (businessObject.eventDefinitions && businessObject.eventDefinitions.length > 0) {
      const timerEventDef = businessObject.eventDefinitions.find(def => def.$type === 'bpmn:TimerEventDefinition');
      if (timerEventDef && timerEventDef.timeDuration) {
        time = timerEventDef.timeDuration.body || '';
      }
    }

    const userTasks = Array.isArray(businessObject.UserTask) ? businessObject.UserTask : [businessObject.UserTask || ''];
    const numberOfExecutions = businessObject.NumberOfExecutions || 1;
    const minimumTime = businessObject.minimumTime || 0;
    const maximumTime = businessObject.maximumTime || 0;
    const loopParameter = businessObject.loopParameter || 'undefined';
    const loopCharacteristics = businessObject.loopCharacteristics || 'undefined';
    const multiInstance = businessObject.loopCharacteristics?.isSequential ?? 'undefined';
    const AdditionalIntegerParameter = businessObject.AdditionalIntegerParameter || 0;

    let instance = '';  
    let userWithRole = {};
    let userWithoutRole = [];
    let userWithoutRoleSet = new Set();
    let frequency = 0;
    let containedElements = businessObject.flowNodeRef 
      ? businessObject.flowNodeRef.map(node => node.id) 
      : [];

    if (e.type === 'bpmn:Collaboration') {
      if (businessObject) {
        if (businessObject.instance !== undefined) {
          instance = businessObject.instance;
        }
      }
    } else if (e.type === 'bpmn:Participant') {
      const processRef = businessObject.processRef;
    
      const participantFrequency = businessObject.frequency || businessObject.get('participantWithoutLane:frequency');
      if (participantFrequency !== undefined) {
        frequency = participantFrequency;
      }
    
      if (processRef) {
        if (processRef.flowElements) {
          containedElements = processRef.flowElements.map(node => node.id);
        }
    
        if (processRef.laneSets) {
          processRef.laneSets.forEach(laneSet => {
            laneSet.lanes.forEach(lane => {
              if (lane.flowNodeRef) {
                lane.flowNodeRef.forEach(node => {
                  containedElements.push(node.id);
                });
              }
            });
          });
        }
      }
      if (businessObject.userWithoutRole) {
        businessObject.userWithoutRole.forEach(role => userWithoutRoleSet.add(role.trim()));
      }
      userWithoutRole = Array.from(userWithoutRoleSet);
    } else if (e.type === 'bpmn:Lane') {
      if (businessObject.userWithoutRole) {
        businessObject.userWithoutRole.forEach(role => userWithoutRoleSet.add(role.trim()));
      }
      containedElements = businessObject.flowNodeRef ? 
        businessObject.flowNodeRef.map(node => node.id) : [];
      userWithoutRole = Array.from(userWithoutRoleSet);
    } else if (e.type === 'bpmn:Process') {
      if (businessObject.instance !== undefined) {
        instance = businessObject.instance;
      }
      if (businessObject.userWithRole) {
        userWithRole = businessObject.userWithRole;
      }
      if (businessObject.userWithoutRole) {
        userWithoutRole = businessObject.userWithoutRole;
        userWithoutRole = [...new Set(userWithoutRole)];
      }
      if (businessObject.frequency !== undefined) {
        frequency = businessObject.frequency;
      }
    } else {
      instance = businessObject.instance || '';
    }

    return {
      id_model: id_model,
      id_bpmn: businessObject.id,
      name: businessObject.name || '',
      type: businessObject.$type || '',
      Mth: isServiceTask ? (businessObject.Mth || 0) : 0,
      P: isServiceTask ? (businessObject.P || 0) : 0,
      User: isServiceTask ? (businessObject.User || '') : '',
      UserTask: (isTask || isUserTask) ? (userTasks.join(', ') || '') : '',
      Log: businessObject.Log || '',
      SubTasks: subTasks,
      subElement: subElement,
      superElement: superElement,
      Instances: isProcess || isCollaboration ? (instance || 0) : 0,
      Frequency: isProcess || isParticipant ? (frequency || 0) : 0,
      PercentageOfBranches: percentageOfBranches,
      NumberOfExecutions: numberOfExecutions,
      MinimumTime: minimumTime,
      MaximumTime: maximumTime,
      UserInstance: instance,
      time: time,
      userWithoutRole: (isProcess || isLane || isParticipant) ? userWithoutRole : '',
      userWithRole: Object.entries(businessObject.userWithRole || {}).map(([role, users]) => ({
        role,
        users: Array.isArray(users) ? users : [users]
    })),    
      type: type,
      loopParameter: loopParameter,
      loopCharacteristics: loopCharacteristics,
      multiInstance: multiInstance,
      AdditionalIntegerParameter: AdditionalIntegerParameter,
      containedElements: containedElements,
    };
  });
}

function exportToEsper(bpmnModeler) {
  return new Promise((resolve, reject) => {
    try {
      const elements = getAllRelevantTasks(bpmnModeler);

      let content = '### Esper Rules Export ###\n\n';
      elements.forEach(element => {

        if (element.type === 'bpmn:StartEvent' && 
            element.businessObject &&
            element.businessObject.eventDefinitions &&
            element.businessObject.eventDefinitions.length > 0 &&
            element.businessObject.eventDefinitions[0].$type === 'bpmn:MessageEventDefinition') {
          content += `Element: [type=bpmn:MessageStartEvent, `;
        } else {
          content += `Element: [type=${element.type}, `;
        }

        content += `name="${element.name || 'Unnamed'}", `;
        content += `id_bpmn="${element.id_bpmn || 'Unknown'}", `; 
       
        if (element.time) {
          content += `time=${element.time}, `;
        }

        if (element.type === 'bpmn:SequenceFlow' || element.type === 'bpmn:MessageFlow' ||
          element.type === 'bpmn:DataObjectReference' || element.type === 'bpmn:BoundaryEvent' ||
          element.type === 'bpmn:DataInputAssociation' || element.type === 'bpmn:DataOutputAssociation') {

            if (element.PercentageOfBranches && element.PercentageOfBranches !== 'N/A') {
              content += `percentageOfBranches=${element.PercentageOfBranches}, `;
            }
          
          const superElement = typeof element.superElement === 'string' 
            ? element.superElement 
            : (Array.isArray(element.superElement) ? element.superElement.join(', ') : 'No Super Element');
          const subElement = element.subElement || 'No Sub Element';

          content += `superElement="${superElement}", `;
          content += `subElement="${subElement}"]\n`;
        } else if (element.type === 'bpmn:Task' || element.type === 'bpmn:UserTask' || element.type === 'bpmn:ManualTask'
          || element.type === 'bpmn:SendTask' || element.type === 'bpmn:ReceiveTask' || element.type === 'bpmn:BusinessRuleTask'
          || element.type === 'bpmn:ScriptTask' || element.type === 'bpmn:CallActivity' || element.type === 'bpmn:ServiceTask'
        ) {
          content += `userTask="${element.UserTask || '""'}", `;
          content += `numberOfExecutions=${element.NumberOfExecutions}, `;
          content += `minimumTime=${element.MinimumTime}, `;
          content += `maximumTime=${element.MaximumTime}, `;
          if(element.loopParameter !== 'undefined'){
            content += `loopParameter={"${element.loopParameter}":${element.AdditionalIntegerParameter}}, `;
          }
          if (element.loopCharacteristics?.isSequential !== undefined) {
            content += `multiInstanceType="${element.loopCharacteristics.isSequential ? 'true' : 'false'}", `;
        }               
          const subTasks = element.SubTasks ? element.SubTasks.join(', ') : 'No SubTasks';
          content += `subTask="${subTasks}"]\n`;
        } else if (element.type === 'bpmn:Collaboration') {
          content += `instances=${element.Instances}]\n`;
        } else if (element.type === 'bpmn:Lane') {
          const userWithoutRole = Array.isArray(element.userWithoutRole)
            ? element.userWithoutRole.map(user => `"${user}"`).join(', ')
            : '""';
          
          const containedElements = element.containedElements && element.containedElements.length > 0
            ? element.containedElements.map(el => `"${el}"`).join(', ')
            : '""';
          
          content += `userWithoutRole=[${userWithoutRole}], containedElements=[${containedElements}]]\n`;
        } else if (element.type === 'bpmn:Process') {
          content += `instances=${element.Instances}, `;
          content += `frequency=${element.Frequency}, `;
        
          const userWithoutRole = Array.isArray(element.userWithoutRole) 
            ? element.userWithoutRole.map(user => `"${user}"`).join(', ')
            : '""';
          content += `userWithoutRole=[${userWithoutRole}], `;
        
          const userWithRole = element.userWithRole
            ? element.userWithRole
                .map((pair) => {
                  if (!pair.key || !pair.value) {
                    console.warn('Formato inesperado en ModdleElement:', pair);
                    return '';
                  }
                  const role = pair.key;
                  const users = pair.value.split(',').map((u) => u.trim());
                  return `"${role}": [${users.map((u) => `"${u}"`).join(', ')}]`;
                })
                .filter((entry) => entry !== '')
                .join(', ')
            : '{}';
        
          content += `userWithRole={${userWithRole}}]\n`;
        } else if (element.type === 'bpmn:Participant') {
          const userWithoutRole = Array.isArray(element.userWithoutRole)
            ? element.userWithoutRole.map(user => `"${user}"`).join(', ')
            : '""';
        
          const containedElements = Array.isArray(element.containedElements) 
            ? element.containedElements.map(el => `"${el}"`).join(', ')
            : '""';
          
          content += `frequency=${element.Frequency}, userWithoutRole=[${userWithoutRole}], containedElements=[${containedElements}]]\n`;
      }  else {
          const subTasks = element.SubTasks ? element.SubTasks.join(', ') : 'No SubTasks';
          content += `subTask="${subTasks}"]\n`;
        }
      });

      if (elements.length === 0) {
        content += 'No elements generated.\n';
      }

      resolve(content);
    } catch (err) {
      reject(err);
    }
  });
}

module.exports = {
  exportToEsper
};
