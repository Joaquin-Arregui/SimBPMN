const axios = require('axios');

function getSecurityTasks(bpmnModeler) {
  var elementRegistry = bpmnModeler.get('elementRegistry');
  var definitions = bpmnModeler.get('canvas').getRootElement().businessObject.$parent;
  var id_model = definitions.diagrams[0].id;
  var serviceTasks = elementRegistry.filter(e => e.type === 'bpmn:ServiceTask');
  var serviceTaskBusinessObjects = serviceTasks.map(e => e.businessObject);
  var res = [];

  serviceTaskBusinessObjects.forEach(function(element) {
    var list = element.outgoing;
    var subTasks = [];

    if (!list || list.length === 0) {
      console.warn(`No hay conexiones salientes (outgoing) para la tarea: ${element.id}`);
    } else {
      list.forEach(function(task) {
        if (task.targetRef) {
          const subTaskElement = elementRegistry.get(task.targetRef.id);

          if (subTaskElement && subTaskElement.businessObject) {
            const targetType = subTaskElement.businessObject.$type;

            let userTask = '""';
            let numberOfExecutions = '1';
            let averageTimeEstimate = 'N/A';
            let instance = 'N/A';
            if (targetType === 'bpmn:UserTask' || targetType === 'bpmn:Task') {
              const bo = subTaskElement.businessObject;
              userTask = bo.userTask || bo.UserTask || bo.assignee || bo.candidateUsers || bo.name || 'Unknown';
              numberOfExecutions = bo.numberOfExecutions || 'N/A';
              averageTimeEstimate = bo.averageTimeEstimate || 'N/A';
              instance = bo.instance || 'N/A';
            }

            subTasks.push({
              taskId: subTaskElement.id,
              UserTask: userTask,
              NumberOfExecutions: numberOfExecutions,
              AverageTimeEstimate: averageTimeEstimate,
              Instance: instance
            });
          } else {
            console.warn(`El targetRef existe pero no tiene un businessObject para la tarea con id: ${task.targetRef.id}`);
            subTasks.push({
              taskId: task.targetRef.id,
              UserTask: 'N/A',
              NumberOfExecutions: 'N/A',
              AverageTimeEstimate: 'N/A',
              Instance: 'N/A'
            });
          }
        } else {
          console.warn(`No se encontró targetRef para la tarea con id: ${task.id}`);
        }
      });
    }

    var isBod = element.securityType === 'BoD';
    var isSod = element.securityType === 'SoD';
    var isUoc = element.securityType === 'UoC';
    var st = {
      id_model: id_model,
      id_bpmn: element.id,
      Bod: isBod ? true : false,
      Sod: isSod ? true : false,
      Uoc: isUoc ? true : false,
      Mth: element.Mth || 0,
      P: element.P || 0,
      User: element.User || '',
      Log: element.Log || '',
      NumberOfExecutions: element.numberOfExecutions || 'N/A',
      AverageTimeEstimate: element.averageTimeEstimate || 'N/A',
      Instance: element.instance || 'N/A',
      SubTasks: subTasks.length > 0 ? subTasks : []
    };
    res.push(st);
  });
  return res;
}

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
    const securityType = businessObject.securityType || '';
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
    let security = false; 
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
        if (businessObject.security !== undefined) {
          security = businessObject.security;
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
      if (businessObject.security !== undefined) {
        security = businessObject.security;
      }
    } else {
      instance = businessObject.instance || '';
    }

    return {
      id_model: id_model,
      id_bpmn: businessObject.id,
      name: businessObject.name || '',
      type: businessObject.$type || '',
      Bod: securityType === 'BoD',
      Sod: securityType === 'SoD',
      Uoc: securityType === 'UoC',
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
      security: security,
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
        } else if (element.type === 'bpmn:ServiceTask' && element.Uoc) {
          content += `sodSecurity=${element.Sod}, `;
          content += `bodSecurity=${element.Bod}, `;
          content += `uocSecurity=${element.Uoc}, `;
          content += `mth=${element.Mth}, `;
          const subTasks = element.SubTasks ? element.SubTasks.join(', ') : 'No SubTasks';
          content += `subTask="${subTasks}"]\n`;
        } else if (element.type === 'bpmn:ServiceTask') {
          content += `sodSecurity=${element.Sod}, `;
          content += `bodSecurity=${element.Bod}, `;
          content += `uocSecurity=${element.Uoc}, `;
          const subTasks = element.SubTasks ? element.SubTasks.join(', ') : 'No SubTasks';
          content += `subTask="${subTasks}"]\n`;
        } else if (element.type === 'bpmn:Task' || element.type === 'bpmn:UserTask' || element.type === 'bpmn:ManualTask'
          || element.type === 'bpmn:SendTask' || element.type === 'bpmn:ReceiveTask' || element.type === 'bpmn:BusinessRuleTask'
          || element.type === 'bpmn:ScriptTask' || element.type === 'bpmn:CallActivity'
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
          content += `instances=${element.Instances}, `;
          content += `security=${element.security}]\n`;
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
        
          content += `userWithRole={${userWithRole}}, `;
          content += `security=${element.security}]\n`;
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

function getTaskById(bpmnModeler, taskId) {
  const elementRegistry = bpmnModeler.get('elementRegistry');
  const element = elementRegistry.get(taskId);
  return element ? element.businessObject : null;
}

function esperRules(bpmnModeler) {
  return new Promise((resolve, reject) => {
    try {
      const elements = getAllRelevantTasks(bpmnModeler);
      const triggeredRules = [];
      elements.filter(element => element.type === "bpmn:ServiceTask").forEach(element => {
        const subTasks = element.SubTasks
          ? element.SubTasks.map(id => getTaskById(bpmnModeler, id)).filter(st => st !== null)
          : [];

        const isBoD = element.Bod === true;
        const isSoD = element.Sod === true;
        const isUoC = element.Uoc === true;

        const triggeredRuleData = {
          id_bpmn: element.id_bpmn || 'Unknown',
          triggeredMessages: []
        };
        if (isBoD) {
          message = `[BOD MONITOR] Binding of Duty rule detected:\n` +
            `- Parent Task ID: ${element.id_bpmn}\n`;
          for(let i = 0; i<subTasks.length; i++) {
            subTask = subTasks[i];
            const subTaskId = subTask.id;
            const user = subTask.UserTask;
            message = message +
            `- SubTask ${i} ID: ${subTaskId} - User ID: ${user}\n`;
          }
          message = message +
          `- Expected: The same user should perform the tasks.\n`
          triggeredRuleData.triggeredMessages.push(message);
        }
        if (isSoD) {
          message = `[SOD MONITOR] Separation of Duties rule detected:\n` +
            `- Parent Task ID: ${element.id_bpmn}\n`;
          for(let i = 0; i<subTasks.length; i++) {
            subTask = subTasks[i];
            const subTaskId = subTask.id;
            const user = subTask.UserTask;
            message = message +
            `- SubTask ${i} ID: ${subTaskId} - User ID: ${user}\n`;
          }
          message = message +
          `- Expected: Different users should perform the tasks.\n`
          triggeredRuleData.triggeredMessages.push(message);
        }
        if (isUoC) {
          message = `[UOC MONITOR] Use of Control rule detected:\n` +
            `- Parent Task ID: ${element.id_bpmn}\n`;
          for(let i = 0; i<subTasks.length; i++) {
            subTask = subTasks[i];
            const subTaskId = subTask.id;
            const user = subTask.UserTask;
            const numberOfExecutions = subTask.NumberOfExecutions;
            message = message +
            `- SubTask ${i} ID: ${subTaskId} - User ID: ${user} - Number of executions: ${numberOfExecutions}\n`;
          }
          message = message +
          `- Expected: Each user should perform a maximum of ${element.Mth} executions.\n`
          triggeredRuleData.triggeredMessages.push(message);
        }
        if (triggeredRuleData.triggeredMessages.length > 0) {
          triggeredRules.push(triggeredRuleData);
        }
      });
      if (triggeredRules.length === 0) {
        triggeredRules.push({ message: 'No rules detected.' });
      }
      resolve(JSON.stringify(triggeredRules, null, 2));
    } catch (err) {
      reject(err);
    }
  });
}

function deployRules(bpmnModeler) {
  return new Promise((resolve, reject) => {
    try {
      const elements = getAllRelevantTasks(bpmnModeler);

      let eplStatements = "";

      const bodElements = elements.filter(element => element.Bod === true);
      if (bodElements.length > 0) {
        const bodEPL = `"select parent.idBpmn as parentId, "
  "sub1.idBpmn as subTask1Id, sub2.idBpmn as subTask2Id, "
  "sub1.userTask as user1, sub2.userTask as user2, "
  "sub1.instance as instance1 "
  "from Task#keepall as parent, Task#keepall as sub1, Task#keepall as sub2 "
  "where parent.bodSecurity = true "
  "and sub1.userTask is not null and sub2.userTask is not null "
  "and sub1.userTask != sub2.userTask "
  "and sub1.idBpmn != sub2.idBpmn "
  "and sub1.idBpmn in (parent.subTasks) "
  "and sub2.idBpmn in (parent.subTasks) "
  "and sub1.instance = sub2.instance"

--------------------------------------

`;

        eplStatements += bodEPL;
      }

      const sodElements = elements.filter(element => element.Sod === true);
      if (sodElements.length > 0) {
        const sodEPL = `"select parent.idBpmn as parentId, "
  "sub1.idBpmn as subTask1Id, sub2.idBpmn as subTask2Id, "
  "sub1.userTask as userTask1, sub2.userTask as userTask2, "
  "sub1.instance as instance1 "
  "from Task#keepall as parent, Task#keepall as sub1, Task#keepall as sub2 "
  "where parent.sodSecurity = true "
  "and sub1.idBpmn != sub2.idBpmn "
  "and sub1.idBpmn in (parent.subTasks) "
  "and sub2.idBpmn in (parent.subTasks) "
  "and sub1.instance = sub2.instance "
  "and sub1.userTask is not null "
  "and sub2.userTask is not null "
  "and sub1.userTask = sub2.userTask "
  "and sub1.idBpmn < sub2.idBpmn"

--------------------------------------

`;

        eplStatements += sodEPL;
      }
      const uocElements = elements.filter(element => element.Uoc === true);
      if (uocElements.length > 0) {
        const uocEPL = `"select parent.idBpmn as parentId, "
  "sub1.idBpmn as subTaskId, "
  "sub1.userTask as userTask, "
  "sub1.instance as instance1, "
  "sub1.numberOfExecutions as totalExecutions, "
  "parent.mth as parentMth "
  "from Task#keepall as parent, Task#keepall as sub1 "
  "where parent.uocSecurity = true "
  "and sub1.idBpmn in (parent.subTasks) "
  "and sub1.userTask is not null "
  "and sub1.numberOfExecutions > parent.mth "
  "group by parent.idBpmn, sub1.idBpmn, parent.mth, sub1.instance"

--------------------------------------

`;

        eplStatements += uocEPL;
      }
      if (eplStatements.trim() === "") {
        eplStatements = "No relevant rules generated.";
      }
      resolve(eplStatements);
    } catch (err) {
      reject(err);
    }
  });
}

module.exports = {
  getSecurityTasks,
  getAllRelevantTasks,
  esperRules,
  deployRules,
  exportToEsper
};
