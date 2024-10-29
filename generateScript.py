def getPercentOfBranches(elements, gateway):
    possibleElements = []
    percents = []
    for element in elements.values():
        if type(element).__name__ == "BPMNSequenceFlow" and element.superElement == gateway:
            possibleElements.append(element.subElement)
            percents.append(element.percentageOfBranches / 100)
    return possibleElements, percents

def exclusiveGateway(elements, element, script):
    possibleElements, percents = getPercentOfBranches(elements, element.id_bpmn)
    functionStr = f"""
def {element.id_bpmn}(env, name):
    selectedElement = random.choices({possibleElements}, {percents})[0]
    with open('files/results_{next(iter(elements))}.txt', 'a') as f:
        f.write(f'''
{{name}}: [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, subTask="{{selectedElement}}", startTime={{env.now}}]''')
    yield env.timeout(0)
    return selectedElement
    """
    extendedScript = script + functionStr
    for elem in possibleElements:
        if ('def ' + elem + '(env, name)') not in script:
            extendedScript = generateFunction(elements, elem, extendedScript)
    return extendedScript

def parallelGateway(elements, element, script):
    possibleElements = element.subTask
    functionStr = f"""
def {element.id_bpmn}(env, name):
    strSelectedElements = ", ".join({possibleElements})
    with open('files/results_{next(iter(elements))}.txt', 'a') as f:
        f.write(f'''
{{name}}: [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, subTask="{{strSelectedElements}}", startTime={{env.now}}]''')
    yield env.timeout(0)
    return {possibleElements}
    """
    extendedScript = script + functionStr
    for elem in possibleElements:
        if ('def ' + elem + '(env, name)') not in script:
            extendedScript = generateFunction(elements, elem, extendedScript)
    return extendedScript

def inclusiveGateway(elements, element, script):
    possibleElements, percents = getPercentOfBranches(elements, element.id_bpmn)
    functionStr = f"""
def {element.id_bpmn}(env, name):
    elements = {possibleElements}
    percents = {percents}
    selectedElements = [element for element, percent in zip(elements, percents) if random.random() < percent]
    if not selectedElements:
        selectedElements = random.choices(elements, weights=percents, k=1)
    strSelectedElements = ", ".join(selectedElements)
    with open('files/results_{next(iter(elements))}.txt', 'a') as f:
        f.write(f'''
{{name}}: [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, subTask="{{strSelectedElements}}", startTime={{env.now}}]''')
    yield env.timeout(0)
    return selectedElements
    """
    extendedScript = script + functionStr
    for elem in possibleElements:
        if ('def ' + elem + '(env, name)') not in script:
            extendedScript = generateFunction(elements, elem, extendedScript)
    return extendedScript

def eventBasedGateway(elements, element, script): 
    possibleElements = element.subTask
    functionStr = f"""
def {element.id_bpmn}(env, name):
    event_completions = []
    event_processes = []
    for elem in {possibleElements}:
        completion_event = env.event()
        event_proc = env.process(globals()[elem](env, name, completion_event))
        event_processes.append(event_proc)
        event_completions.append(completion_event)
    result = yield simpy.AnyOf(env, event_completions)
    for i, event in enumerate(event_completions):
        if event in result.events:
            next_task = event.value
            selected_event = {possibleElements}[i]
            with open('files/results_{next(iter(elements))}.txt', 'a') as f:
                f.write(f'''
{{name}}: [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, subTask="{{selected_event}}", startTime={{env.now}}]''')
            for j, proc in enumerate(event_processes):
                if j != i:
                    proc.interrupt()
            break
    return next_task
    """
    extendedScript = script + functionStr
    for elem in possibleElements:
        if ('def ' + elem + '(env, name') not in script:
            extendedScript = generateFunction(elements, elem, extendedScript, event_based=True)
    return extendedScript

def generalTask(elements, element, script):
    functionStr = f"""
def {element.id_bpmn}(env, name):
    TaskName = '{element.id_bpmn}'
    start_standBy = env.now
    possibleUsers = {element.userTask}
    if possibleUsers is None:
        possibleUsers = userPool
    possibleUsers = resolve_possible_users(possibleUsers)
    available_users = [user for user in possibleUsers if user_resources[user].count < user_resources[user].capacity]
    while not available_users:
        yield env.timeout(1)
        available_users = [user for user in possibleUsers if user_resources[user].count < user_resources[user].capacity]
    if available_users:
        userTask = min(available_users, key=lambda u: user_assignments[u])
        user_assignments[userTask] += 1
        request = user_resources[userTask].request()
        yield request
        try:
            time = resolve_task_time('{element.id_bpmn}', {element.maximumTime}, {element.minimumTime}, {element.numberOfExecutions}, userTask)
            if env.now > start_standBy:
                with open('files/results_{next(iter(elements))}.txt', 'a') as f:
                    f.write(f'''
{{name}}: [type=StandBy, id_bpmn={{TaskName}}, startTime={{start_standBy}}, stopTime={{env.now}}, time={{env.now-start_standBy}}]''')
            with open('files/results_{next(iter(elements))}.txt', 'a') as f:
                f.write(f'''
{{name}}: [type=bpmn:Task, name=Unnamed, id_bpmn={{TaskName}}, userTask={{userTask}}, numberOfExecutions={element.numberOfExecutions}, time={{time}}, subTask="{element.subTask}", startTime={{env.now}}]''')
            yield env.timeout(time)
        finally:
            user_resources[userTask].release(request)
    return '{element.subTask}'
"""
    return generateFunction(elements, element.subTask, script + functionStr)


def sendTask(elements, element, script):
    functionStr = f"""
def {element.id_bpmn}(env, name):
    TaskName = '{element.id_bpmn}'
    start_standBy = env.now
    possibleUsers = {element.userTask}
    if possibleUsers is None:
        possibleUsers = userPool
    possibleUsers = resolve_possible_users(possibleUsers)
    available_users = [user for user in possibleUsers if user_resources[user].count < user_resources[user].capacity]
    while not available_users:
        yield env.timeout(1)
        available_users = [user for user in possibleUsers if user_resources[user].count < user_resources[user].capacity]
    if available_users:
        userTask = min(available_users, key=lambda u: user_assignments[u])
        user_assignments[userTask] += 1
        request = user_resources[userTask].request()
        yield request
        try:
            time = resolve_task_time('{element.id_bpmn}', {element.maximumTime}, {element.minimumTime}, {element.numberOfExecutions}, userTask)
            if env.now > start_standBy:
                with open('files/results_{next(iter(elements))}.txt', 'a') as f:
                    f.write(f'''
{{name}}: [type=StandBy, id_bpmn={{TaskName}}, startTime={{start_standBy}}, stopTime={{env.now}}, time={{env.now-start_standBy}}]''')
            with open('files/results_{next(iter(elements))}.txt', 'a') as f:
                f.write(f'''
{{name}}: [type=bpmn:Task, name=Unnamed, id_bpmn={{TaskName}}, userTask={{userTask}}, numberOfExecutions={element.numberOfExecutions}, time={{time}}, subTask="{element.subTask}", startTime={{env.now}}]''')
            yield env.timeout(time)
            if (TaskName, '{element.messageDestiny}', name) not in message_events:
                message_events[(TaskName, '{element.messageDestiny}', name)] = env.event()
            message_events[(TaskName, '{element.messageDestiny}', name)].succeed()
            message_events[(TaskName, '{element.messageDestiny}', name)] = env.event()
        finally:
            user_resources[userTask].release(request)
    return '{element.subTask}'
"""
    return generateFunction(elements, element.subTask, script + functionStr)


def recieveTask(elements, element, script):
    functionStr = f"""
def {element.id_bpmn}(env, name):
    TaskName = '{element.id_bpmn}'
    if ('{element.messageOrigin}', TaskName, name) not in message_events:
        message_events[('{element.messageOrigin}', TaskName, name)] = env.event()
    start_standby_message = env.now
    yield message_events[('{element.messageOrigin}', TaskName, name)]
    end_standby_message = env.now
    duration_standby_message = end_standby_message - start_standby_message
    if duration_standby_message > 0:
        with open('files/results_{next(iter(elements))}.txt', 'a') as f:
            f.write(f'''
{{name}}: [type=StandByMessage, id_bpmn={{TaskName}}, startTime={{start_standby_message}}, stopTime={{end_standby_message}}, time={{duration_standby_message}}]''')
    start_standBy = env.now
    possibleUsers = {element.userTask}
    if possibleUsers is None:
        possibleUsers = userPool
    possibleUsers = resolve_possible_users(possibleUsers)
    available_users = [user for user in possibleUsers if user_resources[user].count < user_resources[user].capacity]
    while not available_users:
        yield env.timeout(1)
        available_users = [user for user in possibleUsers if user_resources[user].count < user_resources[user].capacity]
    if available_users:
        userTask = min(available_users, key=lambda u: user_assignments[u])
        user_assignments[userTask] += 1
        request = user_resources[userTask].request()
        yield request
        try:
            time = resolve_task_time('{element.id_bpmn}', {element.maximumTime}, {element.minimumTime}, {element.numberOfExecutions}, userTask)
            if env.now > start_standBy:
                with open('files/results_{next(iter(elements))}.txt', 'a') as f:
                    f.write(f'''
{{name}}: [type=StandBy, id_bpmn={{TaskName}}, startTime={{start_standBy}}, stopTime={{env.now}}, time={{env.now-start_standBy}}]''')
            with open('files/results_{next(iter(elements))}.txt', 'a') as f:
                f.write(f'''
{{name}}: [type=bpmn:Task, name=Unnamed, id_bpmn={{TaskName}}, userTask={{userTask}}, numberOfExecutions={element.numberOfExecutions}, time={{time}}, subTask="{element.subTask}", startTime={{env.now}}]''')
            yield env.timeout(time)
        finally:
            user_resources[userTask].release(request)
    return '{element.subTask}'
"""
    return generateFunction(elements, element.subTask, script + functionStr)

def intermediateThrowEvent(elements, element, script):
    functionStr = f"""
def {element.id_bpmn}(env, name):
    with open('files/results_{next(iter(elements))}.txt', 'a') as f:
        f.write(f'''
{{name}}: [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, subTask="{element.subTask}", startTime={{env.now}}]''')
    yield env.timeout(0)
    return '{element.subTask}'
    """
    return generateFunction(elements, element.subTask, script + functionStr)

def messageIntermediateCatchEvent(elements, element, script, event_based):
    if event_based:
        functionStr = f"""
def {element.id_bpmn}(env, name, completion_event):
    TaskName = '{element.id_bpmn}'
    if ('{element.messageOrigin}', TaskName, name) not in message_events:
        message_events[('{element.messageOrigin}', TaskName, name)] = env.event()
    start_standby_message = env.now
    try:
        yield message_events[('{element.messageOrigin}', TaskName, name)]
        end_standby_message = env.now
        duration_standby_message = end_standby_message - start_standby_message
        if duration_standby_message > 0:
            with open('files/results_{next(iter(elements))}.txt', 'a') as f:
                f.write(f'''
{{name}}: [type=StandByMessage, id_bpmn={{TaskName}}, startTime={{start_standby_message}}, stopTime={{end_standby_message}}, time={{duration_standby_message}}]''')
        completion_event.succeed('{element.subTask}')
        with open('files/results_{next(iter(elements))}.txt', 'a') as f:
            f.write(f'''
{{name}}: [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, subTask="{element.subTask}", startTime={{env.now}}]''')
    except simpy.Interrupt:
        pass
"""
    else:
        functionStr = f"""
def {element.id_bpmn}(env, name):
    TaskName = '{element.id_bpmn}'
    if ('{element.messageOrigin}', TaskName, name) not in message_events:
        message_events[('{element.messageOrigin}', TaskName, name)] = env.event()
    start_standby_message = env.now
    yield message_events[('{element.messageOrigin}', TaskName, name)]
    end_standby_message = env.now
    duration_standby_message = end_standby_message - start_standby_message
    if duration_standby_message > 0:
        with open('files/results_{next(iter(elements))}.txt', 'a') as f:
            f.write(f'''
{{name}}: [type=StandByMessage, id_bpmn={{TaskName}}, startTime={{start_standby_message}}, stopTime={{end_standby_message}}, time={{duration_standby_message}}]''')
    with open('files/results_{next(iter(elements))}.txt', 'a') as f:
        f.write(f'''
{{name}}: [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, subTask="{element.subTask}", startTime={{env.now}}]''')
    return '{element.subTask}'
"""
    return generateFunction(elements, element.subTask, script + functionStr)

def messageIntermediateThrowEvent(elements, element, script):
    functionStr = f"""
def {element.id_bpmn}(env, name):
    TaskName = '{element.id_bpmn}'
    with open('files/results_{next(iter(elements))}.txt', 'a') as f:
        f.write(f'''
{{name}}: [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, subTask="{element.subTask}", startTime={{env.now}}]''')
    yield env.timeout(0)
    if (TaskName, '{element.messageDestiny}', name) not in message_events:
        message_events[(TaskName, '{element.messageDestiny}', name)] = env.event()
    message_events[(TaskName, '{element.messageDestiny}', name)].succeed()
    message_events[(TaskName, '{element.messageDestiny}', name)] = env.event()
    return '{element.subTask}'
    """
    return generateFunction(elements, element.subTask, script + functionStr)

def timerIntermediateCatchEvent(elements, element, script, event_based):
    if event_based:
        functionStr = f"""
def {element.id_bpmn}(env, name, completion_event):
    try:
        yield env.timeout({element.time})
        completion_event.succeed('{element.subTask}')
        with open('files/results_{next(iter(elements))}.txt', 'a') as f:
            f.write(f'''
{{name}}: [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, time={element.time}, subTask="{element.subTask}", startTime={{env.now}}]''')
    except simpy.Interrupt:
        pass
    """
    else:
        functionStr = f"""
def {element.id_bpmn}(env, name):
    with open('files/results_{next(iter(elements))}.txt', 'a') as f:
        f.write(f'''
{{name}}: [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, time={element.time}, subTask="{element.subTask}", startTime={{env.now}}]''')
    yield env.timeout({element.time})
    return '{element.subTask}'
"""
    return generateFunction(elements, element.subTask, script + functionStr)

def endEvent(elements, element, script):
    functionStr = f"""
def {element.id_bpmn}(env, name):
    with open('files/results_{next(iter(elements))}.txt', 'a') as f:
        f.write(f'''
{{name}}: [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, subTask="", startTime={{env.now}}]''')
    yield env.timeout(0)
    """
    return script + functionStr

def generateFunction(elements, elementId, script, event_based=False):
    element = elements[elementId]
    elementType = type(element).__name__
    if elementType == "BPMNExclusiveGateway":
        return exclusiveGateway(elements, element, script)
    elif elementType == "BPMNParallelGateway":
        return parallelGateway(elements, element, script)
    elif elementType == "BPMNInclusiveGateway":
        return inclusiveGateway(elements, element, script)
    elif elementType == "BPMNEventBasedGateway":
        return eventBasedGateway(elements, element, script)
    elif elementType in ["BPMNTask", "BPMNUserTask", "", "BPMNManualTask", "BPMNBusinessRuleTask", "BPMNScriptTask", "BPMNCallActivity"]:
        return generalTask(elements, element, script)
    elif elementType == "BPMNSendTask":
        return sendTask(elements, element, script)
    elif elementType == "BPMNRecieveTask":
        return recieveTask(elements, element, script)
    elif elementType == "BPMNIntermediateThrowEvent":
        return intermediateThrowEvent(elements, element, script)
    elif elementType == "BPMNMessageIntermediateCatchEvent":
        return messageIntermediateCatchEvent(elements, element, script, event_based)
    elif elementType == "BPMNMessageIntermediateThrowEvent":
        return messageIntermediateThrowEvent(elements, element, script)
    elif elementType == "BPMNTimerIntermediateCatchEvent":
        return timerIntermediateCatchEvent(elements, element, script, event_based)
    elif elementType == "BPMNEndEvent":
        return endEvent(elements, element, script)

def serviceTask(elements):
    script = f"""
def checkServiceTasks(name):
    with open('files/results_{next(iter(elements))}.txt', 'r') as f:
        content = f.readlines()"""
    for element in elements.values():
        if not isinstance(element, dict) and element.bpmn_type == 'bpmn:ServiceTask':
            script += f"""
    found1 = False
    activities = {{"""
            subTasks = element.subTask
            for subElement in subTasks:
                script += f"""
        '{subElement}': False,"""
            script = script.rstrip(',')
            script += f"""
    }}
    last_activity_index = -1
    line_index = -1
    for line in content:
        line_index += 1
        if f'{{name}}:' in line and 'id_bpmn={element.id_bpmn}' in line:
            found1 = True
        for activity in activities:
            if f'{{name}}:' in line and f'id_bpmn={{activity}}' in line:
                activities[activity] = True
                last_activity_index = line_index
    number_found = sum(activities.values())
    if not found1 and number_found >= 1 and last_activity_index != -1:
        subtasks_str = ", ".join([activity for activity, found in activities.items() if found])
        new_line = f'''{{name}}: [type={element.bpmn_type}, name={element.name}, id_bpmn={element.id_bpmn}, sodSecurity={element.sodSecurity}, bodSecurity={element.bodSecurity}, uocSecurity={element.uocSecurity}, nu={element.nu}, mth={element.mth}, subTask="{{subtasks_str}}"]\\n'''
        content.insert(last_activity_index + 1, new_line)
    """
    script += f"""
    with open('files/results_{next(iter(elements))}.txt', 'w') as f:
        f.writelines(content)
    """
    return script

def generateScript(elements, process, starts, userPerTask):
    elementProcess = elements[process]
    script = f"""
import simpy
import random

nInstances = {elementProcess.instances}
frequency = {elementProcess.frequency}
rolePool = {elementProcess.userWithRole}
userWithRole = list(set(value for sublist in rolePool.values() for value in sublist))
userWithoutRole = {elementProcess.userWithoutRole}
userPool = userWithRole + userWithoutRole
user_task_count = {{}}
user_assignments = {{user: 0 for user in userPool}}
user_resources = {{}}
message_events = {{}}

def resolve_task_time(task_name, max_time, min_time, executions, user):
    if user not in user_task_count:
        user_task_count[user] = {{}}
    if task_name not in user_task_count[user]:
        user_task_count[user][task_name] = 0

    mu = (min_time+max_time)/2
    sigma = (max_time-min_time)/6
    time = sum(max(min_time, min(random.gauss(mu,sigma), max_time)) for _ in range(executions))
    reduction_factor = 1 - min(0.05 * user_task_count[user][task_name], 0.5)

    user_task_count[user][task_name] += 1
    return round(time * reduction_factor)

def resolve_possible_users(possibleUsers):
    users = []
    for item in possibleUsers:
        if item in rolePool:
            users.extend(rolePool[item])
        elif item in userWithoutRole:
            users.append(item)
        elif item in userWithRole:
            users.append(item)
    return list(set(users))

"""
    startElements = {}
    for start in starts:
        startEvent = elements[start]
        startElements[start] = [startEvent.bpmn_type, startEvent.name, startEvent.id_bpmn, startEvent.subTask]
        script = generateFunction(elements, startEvent.subTask, script)
    if userPerTask:
        scriptServiceTask = serviceTask(elements)
    else:
        scriptServiceTask = ''
    scriptMainFunction = f"""
def process_task(env, name, task_name):
    task_func = globals()[task_name]
    result = yield env.process(task_func(env, name))
    if result:
        if isinstance(result, list):
            for next_task in result:
                env.process(process_task(env, name, next_task))
        else:
            env.process(process_task(env, name, result))

def start_process(env, name, nextTask):
    yield env.process(process_task(env, name, nextTask))

def main(env):
    startEvents = {startElements}
    global user_resources
    user_resources = {{user: simpy.Resource(env, capacity=1) for user in userPool}}
    with open('files/results_{next(iter(elements))}.txt', 'w') as f:
        f.write(f"Element: [type={elementProcess.bpmn_type}, name={elementProcess.name}, id_bpmn={elementProcess.id_bpmn}, instances={{nInstances}}, frequency={{frequency}}, userWithoutRole={{userWithoutRole}}, userWithRole={{rolePool}}]")
    for i in range(nInstances):
        for start in {starts}:
            with open('files/results_{next(iter(elements))}.txt', 'a') as f:
                f.write(f'''
Instance {{i + 1}}: [type={{startEvents[start][0]}}, name={{startEvents[start][1]}}, id_bpmn={{startEvents[start][2]}}, subTask="{{startEvents[start][3]}}", startTime={{env.now}}]''')
            env.process(start_process(env, f'Instance {{i + 1}}', startEvents[start][3]))
        yield env.timeout(frequency)

env = simpy.Environment()
env.process(main(env))
env.run()"""
    if userPerTask:
        scriptMainFunction += f"""
for i in range(nInstances):
    checkServiceTasks(f'Instance {{i + 1}}')"""
    return script + scriptServiceTask + scriptMainFunction, process
