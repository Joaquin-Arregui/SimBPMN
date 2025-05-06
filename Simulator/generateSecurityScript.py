def getPercentOfBranches(elements, gateway):
    possibleElements = {}
    none_elements = []
    for element in elements.values():
        if type(element).__name__ == "BPMNSequenceFlow" and element.superElement == gateway:
            if element.percentageOfBranches is None:
                possibleElements[element.subElement] = None
                none_elements.append(element.subElement)
            else:
                possibleElements[element.subElement] = element.percentageOfBranches / 100
    total_assigned_percent = sum([v for v in possibleElements.values() if v is not None])
    remaining_percent = 1 - total_assigned_percent
    if none_elements:
        equal_percent = remaining_percent / len(none_elements)
        for sub_element in none_elements:
            possibleElements[sub_element] = equal_percent
    return list(possibleElements.keys()), list(possibleElements.values())

def exclusiveGateway(elements, element, script):
    possibleElements, percents = getPercentOfBranches(elements, element.id_bpmn)
    functionStr = f"""
def {element.id_bpmn}(env, name):
    selectedElement = random.choices({possibleElements}, {percents})[0]
    simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="{element.bpmn_type}"/>
            <string key="bpmn:name" value="{element.name}"/>
            <string key="bpmn:id" value="{element.id_bpmn}"/>
            <string key="bpmn:subTask" value="{{selectedElement}}"/>
            <date key="time:timestamp" value="{{env.now}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
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
    simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="{element.bpmn_type}"/>
            <string key="bpmn:name" value="{element.name}"/>
            <string key="bpmn:id" value="{element.id_bpmn}"/>
            <string key="bpmn:subTask" value="{{strSelectedElements}}"/>
            <date key="time:timestamp" value="{{env.now}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
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
    simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="{element.bpmn_type}"/>
            <string key="bpmn:name" value="{element.name}"/>
            <string key="bpmn:id" value="{element.id_bpmn}"/>
            <string key="bpmn:subTask" value="{{selectedElements}}"/>
            <date key="time:timestamp" value="{{env.now}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
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
            simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="{element.bpmn_type}"/>
            <string key="bpmn:name" value="{element.name}"/>
            <string key="bpmn:id" value="{element.id_bpmn}"/>
            <string key="bpmn:subTask" value="{{selected_event}}"/>
            <date key="time:timestamp" value="{{env.now}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
            for j, proc in enumerate(event_processes):
                if j != i:
                    proc.interrupt()
            break
    return next_task
"""
    extendedScript = script + functionStr
    for elem in possibleElements:
        if ('def ' + elem + '(env, name') not in script:
            extendedScript = generateFunction(elements, elem, extendedScript)
    return extendedScript

def generalTask(elements, element, script):
    if element.multiInstanceType == True or (element.multiInstanceType == None and element.loopParameter == None):
        functionStr = f"""
def {element.id_bpmn}(env, name):
    TaskName = '{element.id_bpmn}'
    if TaskName in requiredData.keys():
        dataObjects = requiredData[TaskName]
        start_standBy_data = env.now
        while not all((dataObject, name) in data for dataObject in dataObjects):
            yield env.timeout(1)
        if env.now < start_standBy_data:
            simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="StandByData"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <date key="time:timestamp" value="{{start_standBy_data}}"/>
            <date key="time:endTime" value="{{env.now}}"/>
            <date key="time:duration" value="{{env.now-start_standBy_data}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
    for i in range({element.numberOfExecutions}):
        start_standBy = env.now
        possibleUsers = {element.userTask}
        if possibleUsers is None:
            possibleUsers = userPool
        possibleSecureUsers = resolve_possible_users_security(possibleUsers, TaskName, name)
        available_users = [user for user in possibleSecureUsers if user_resources[user].count < user_resources[user].capacity]
        if available_users == []:
            possibleNormalUsers = resolve_possible_users(possibleUsers, TaskName)
            available_users = [user for user in possibleNormalUsers if user_resources[user].count < user_resources[user].capacity]
        while not available_users:
            yield env.timeout(1)
            available_users = [user for user in possibleNormalUsers if user_resources[user].count < user_resources[user].capacity]
        if available_users:
            userTask = min(available_users, key=lambda u: user_assignments[u])
            user_assignments[userTask] += 1
            if TaskName in security.keys():
                secTasks = security[TaskName]
                for secTask in secTasks.keys():
                    infoSecTask = secTasks[secTask]
                    if infoSecTask[0]:
                        task_users[(secTask, name)].append(userTask)
                    if infoSecTask[1]:
                        task_users[(secTask, name)] = userTask
                    if infoSecTask[2]:
                        if userTask in task_users[(secTask, name, TaskName)]:
                            task_users[(secTask, name, TaskName)][userTask] += 1
                        else:
                            task_users[(secTask, name, TaskName)][userTask] = 1
            request = user_resources[userTask].request()
            yield request
            try:
                time = resolve_task_time('{element.id_bpmn}', {element.maximumTime}, {element.minimumTime}, userTask)
                if env.now < start_standBy:
                    simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="StandBy"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <string key="bpmn:execution" value="{{i+1}}"/>
            <date key="time:timestamp" value="{{start_standBy}}"/>
            <date key="time:endTime" value="{{env.now}}"/>
            <date key="time:duration" value="{{env.now-start_standBy}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
                simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="{element.bpmn_type}"/>
            <string key="bpmn:name" value="{element.name}"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <string key="bpmn:userTask" value="{{userTask}}"/>
            <int key="bpmn:execution" value="{{i+1}}"/>
            <int key="bpmn:time" value="{{time}}"/>
            <string key="bpmn:subTask" value="{element.subTask}"/>
            <date key="time:timestamp" value="{{env.now}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
                yield env.timeout(time)
            finally:
                user_resources[userTask].release(request)
    if TaskName in generatedData.keys():
        dataObjects = generatedData[TaskName]
        for dataObject in dataObjects:
            data.append((dataObject, name))
            simulationResults[name].append(
f'''
        <container key="dataObjects">
            <string key="bpmn:id" value="{{dataObject}}"/>
            <string key="bpmn:name" value="{{dataInfo[dataObject]}}"/>
            <date key="time:generationTime" value="{{env.now}}"/>
        </container>''')
    for key, values in gatewayConnections.items():
        if TaskName in values:
            if (key, name) in gatewayOccurrences.keys():
                gatewayOccurrences[(key, name)] += 1
            else:
                gatewayOccurrences[(key, name)] = 1
    return '{element.subTask}'
"""
    elif element.multiInstanceType == False:
        functionStr = f"""
def {element.id_bpmn}(env, name):
    def executeTask(env, TaskName, name, executionNumber):
        start_standBy = env.now
        possibleUsers = {element.userTask}
        if possibleUsers is None:
            possibleUsers = userPool
        possibleSecureUsers = resolve_possible_users_security(possibleUsers, TaskName, name)
        available_users = [user for user in possibleSecureUsers if user_resources[user].count < user_resources[user].capacity]
        if available_users == []:
            possibleNormalUsers = resolve_possible_users(possibleUsers, TaskName)
            available_users = [user for user in possibleNormalUsers if user_resources[user].count < user_resources[user].capacity]
        while not available_users:
            yield env.timeout(1)
            available_users = [user for user in possibleNormalUsers if user_resources[user].count < user_resources[user].capacity]
        if available_users:
            userTask = min(available_users, key=lambda u: user_assignments[u])
            user_assignments[userTask] += 1
            if TaskName in security.keys():
                secTasks = security[TaskName]
                for secTask in secTasks.keys():
                    infoSecTask = secTasks[secTask]
                    if infoSecTask[0]:
                        task_users[(secTask, name)].append(userTask)
                    if infoSecTask[1]:
                        task_users[(secTask, name)] = userTask
                    if infoSecTask[2]:
                        if userTask in task_users[(secTask, name, TaskName)]:
                            task_users[(secTask, name, TaskName)][userTask] += 1
                        else:
                            task_users[(secTask, name, TaskName)][userTask] = 1
            request = user_resources[userTask].request()
            yield request
            try:
                time = resolve_task_time('{element.id_bpmn}', {element.maximumTime}, {element.minimumTime}, userTask)
                if env.now < start_standBy:
                    simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="StandBy"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <string key="bpmn:execution" value="{{executionNumber+1}}"/>
            <date key="time:timestamp" value="{{start_standBy}}"/>
            <date key="time:endTime" value="{{env.now}}"/>
            <date key="time:duration" value="{{env.now-start_standBy}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
                simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="{element.bpmn_type}"/>
            <string key="bpmn:name" value="{element.name}"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <string key="bpmn:userTask" value="{{userTask}}"/>
            <int key="bpmn:execution" value="{{executionNumber+1}}"/>
            <int key="bpmn:time" value="{{time}}"/>
            <string key="bpmn:subTask" value="{element.subTask}"/>
            <date key="time:timestamp" value="{{env.now}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
                yield env.timeout(time)
            finally:
                user_resources[userTask].release(request)
    TaskName = '{element.id_bpmn}'
    if TaskName in requiredData.keys():
        dataObjects = requiredData[TaskName]
        start_standBy_data = env.now
        while not all((dataObject, name) in data for dataObject in dataObjects):
            yield env.timeout(1)
        if env.now < start_standBy_data:
            simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="StandByData"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <date key="time:timestamp" value="{{start_standBy_data}}"/>
            <date key="time:endTime" value="{{env.now}}"/>
            <date key="time:duration" value="{{env.now-start_standBy_data}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
    executionProcesses = []
    for i in range({element.numberOfExecutions}):
        executionProcesses.append(env.process(executeTask(env, TaskName, name, i)))
    yield simpy.AllOf(env, executionProcesses)
    if TaskName in generatedData.keys():
        dataObjects = generatedData[TaskName]
        for dataObject in dataObjects:
            data.append((dataObject, name))
            simulationResults[name].append(
f'''
        <container key="dataObjects">
            <string key="bpmn:id" value="{{dataObject}}"/>
            <string key="bpmn:name" value="{{dataInfo[dataObject]}}"/>
            <date key="time:generationTime" value="{{env.now}}"/>
        </container>''')
    for key, values in gatewayConnections.items():
        if TaskName in values:
            if (key, name) in gatewayOccurrences.keys():
                gatewayOccurrences[(key, name)] += 1
            else:
                gatewayOccurrences[(key, name)] = 1
    return '{element.subTask}'
"""
    elif element.multiInstanceType == None:
        if "Time" in element.loopParameter.keys():
            time = element.loopParameter["Time"]
        else:
            time = 0
        if "Units" in element.loopParameter.keys():
            units = element.loopParameter["Units"]
        else:
            units = -1
        if "Percentage" in element.loopParameter.keys():
            percentage = 1 - element.loopParameter["Percentage"]/100
        else:
            percentage = 1
        functionStr = f"""
def {element.id_bpmn}(env, name):
    TaskName = '{element.id_bpmn}'
    if TaskName in requiredData.keys():
        dataObjects = requiredData[TaskName]
        start_standBy_data = env.now
        while not all((dataObject, name) in data for dataObject in dataObjects):
            yield env.timeout(1)
        if env.now < start_standBy_data:
            simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="StandByData"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <date key="time:timestamp" value="{{start_standBy_data}}"/>
            <date key="time:endTime" value="{{env.now}}"/>
            <date key="time:duration" value="{{env.now-start_standBy_data}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
    units = {units}
    loopStartTime = env.now
    initial = True
    execution = 0
    while ((env.now - loopStartTime < {time}) or ({time}==0)) and (units!=0) and (random.random() < {percentage}) or initial:
        execution = execution + 1
        initial = False
        start_standBy = env.now
        possibleUsers = {element.userTask}
        if possibleUsers is None:
            possibleUsers = userPool
        possibleSecureUsers = resolve_possible_users_security(possibleUsers, TaskName, name)
        available_users = [user for user in possibleSecureUsers if user_resources[user].count < user_resources[user].capacity]
        if available_users == []:
            possibleNormalUsers = resolve_possible_users(possibleUsers, TaskName)
            available_users = [user for user in possibleNormalUsers if user_resources[user].count < user_resources[user].capacity]
        while not available_users:
            yield env.timeout(1)
            available_users = [user for user in possibleNormalUsers if user_resources[user].count < user_resources[user].capacity]
        if available_users:
            userTask = min(available_users, key=lambda u: user_assignments[u])
            user_assignments[userTask] += 1
            if TaskName in security.keys():
                secTasks = security[TaskName]
                for secTask in secTasks.keys():
                    infoSecTask = secTasks[secTask]
                    if infoSecTask[0]:
                        task_users[(secTask, name)].append(userTask)
                    if infoSecTask[1]:
                        task_users[(secTask, name)] = userTask
                    if infoSecTask[2]:
                        if userTask in task_users[(secTask, name, TaskName)]:
                            task_users[(secTask, name, TaskName)][userTask] += 1
                        else:
                            task_users[(secTask, name, TaskName)][userTask] = 1
            request = user_resources[userTask].request()
            yield request
            try:
                time = resolve_task_time('{element.id_bpmn}', {element.maximumTime}, {element.minimumTime}, userTask)
                if env.now < start_standBy:
                    simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="StandBy"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <string key="bpmn:execution" value="{{execution}}"/>
            <date key="time:timestamp" value="{{start_standBy}}"/>
            <date key="time:endTime" value="{{env.now}}"/>
            <date key="time:duration" value="{{env.now-start_standBy}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
                simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="{element.bpmn_type}"/>
            <string key="bpmn:name" value="{element.name}"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <string key="bpmn:userTask" value="{{userTask}}"/>
            <int key="bpmn:execution" value="{{execution}}"/>
            <int key="bpmn:time" value="{{time}}"/>
            <string key="bpmn:subTask" value="{element.subTask}"/>
            <date key="time:timestamp" value="{{env.now}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
                yield env.timeout(time)
            finally:
                user_resources[userTask].release(request)
                units = units - 1
    if TaskName in generatedData.keys():
        dataObjects = generatedData[TaskName]
        for dataObject in dataObjects:
            data.append((dataObject, name))
            simulationResults[name].append(
f'''
        <container key="dataObjects">
            <string key="bpmn:id" value="{{dataObject}}"/>
            <string key="bpmn:name" value="{{dataInfo[dataObject]}}"/>
            <date key="time:generationTime" value="{{env.now}}"/>
        </container>''')
    for key, values in gatewayConnections.items():
        if TaskName in values:
            if (key, name) in gatewayOccurrences.keys():
                gatewayOccurrences[(key, name)] += 1
            else:
                gatewayOccurrences[(key, name)] = 1
    return '{element.subTask}'
"""
    return generateFunction(elements, element.subTask, script + functionStr)


def sendTask(elements, element, script):
    if element.multiInstanceType == True or (element.multiInstanceType == None and element.loopParameter == None):
        functionStr = f"""
def {element.id_bpmn}(env, name):
    TaskName = '{element.id_bpmn}'
    if TaskName in requiredData.keys():
        dataObjects = requiredData[TaskName]
        start_standBy_data = env.now
        while not all((dataObject, name) in data for dataObject in dataObjects):
            yield env.timeout(1)
        if env.now < start_standBy_data:
            simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="StandByData"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <date key="time:timestamp" value="{{start_standBy_data}}"/>
            <date key="time:endTime" value="{{env.now}}"/>
            <date key="time:duration" value="{{env.now-start_standBy_data}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
    for i in range({element.numberOfExecutions}):
        start_standBy = env.now
        possibleUsers = {element.userTask}
        if possibleUsers is None:
            possibleUsers = userPool
        possibleSecureUsers = resolve_possible_users_security(possibleUsers, TaskName, name)
        available_users = [user for user in possibleSecureUsers if user_resources[user].count < user_resources[user].capacity]
        if available_users == []:
            possibleNormalUsers = resolve_possible_users(possibleUsers, TaskName)
            available_users = [user for user in possibleNormalUsers if user_resources[user].count < user_resources[user].capacity]
        while not available_users:
            yield env.timeout(1)
            available_users = [user for user in possibleNormalUsers if user_resources[user].count < user_resources[user].capacity]
        if available_users:
            userTask = min(available_users, key=lambda u: user_assignments[u])
            user_assignments[userTask] += 1
            if TaskName in security.keys():
                secTasks = security[TaskName]
                for secTask in secTasks.keys():
                    infoSecTask = secTasks[secTask]
                    if infoSecTask[0]:
                        task_users[(secTask, name)].append(userTask)
                    if infoSecTask[1]:
                        task_users[(secTask, name)] = userTask
                    if infoSecTask[2]:
                        if userTask in task_users[(secTask, name, TaskName)]:
                            task_users[(secTask, name, TaskName)][userTask] += 1
                        else:
                            task_users[(secTask, name, TaskName)][userTask] = 1
            request = user_resources[userTask].request()
            yield request
            try:
                time = resolve_task_time('{element.id_bpmn}', {element.maximumTime}, {element.minimumTime}, userTask)
                if env.now < start_standBy:
                    simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="StandBy"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <string key="bpmn:execution" value="{{i+1}}"/>
            <date key="time:timestamp" value="{{start_standBy}}"/>
            <date key="time:endTime" value="{{env.now}}"/>
            <date key="time:duration" value="{{env.now-start_standBy}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
                simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="{element.bpmn_type}"/>
            <string key="bpmn:name" value="{element.name}"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <string key="bpmn:messageDestiny" value="{element.messageDestiny}"/>
            <string key="bpmn:userTask" value="{{userTask}}"/>
            <int key="bpmn:execution" value="{{i+1}}"/>
            <int key="bpmn:time" value="{{time}}"/>
            <string key="bpmn:subTask" value="{element.subTask}"/>
            <date key="time:timestamp" value="{{env.now}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
                yield env.timeout(time)
            finally:
                user_resources[userTask].release(request)
                if (TaskName, '{element.messageDestiny}', i+1, name) not in message_events:
                    message_events.append((TaskName, '{element.messageDestiny}', i+1, name))
    if TaskName in generatedData.keys():
        dataObjects = generatedData[TaskName]
        for dataObject in dataObjects:
            data.append((dataObject, name))
            simulationResults[name].append(
f'''
        <container key="dataObjects">
            <string key="bpmn:id" value="{{dataObject}}"/>
            <string key="bpmn:name" value="{{dataInfo[dataObject]}}"/>
            <date key="time:generationTime" value="{{env.now}}"/>
        </container>''')
    for key, values in gatewayConnections.items():
        if TaskName in values:
            if (key, name) in gatewayOccurrences.keys():
                gatewayOccurrences[(key, name)] += 1
            else:
                gatewayOccurrences[(key, name)] = 1
    return '{element.subTask}'
"""
    elif element.multiInstanceType == False:
        functionStr = f"""
def {element.id_bpmn}(env, name):
    def executeTask(env, TaskName, name, executionNumber):
        start_standBy = env.now
        possibleUsers = {element.userTask}
        if possibleUsers is None:
            possibleUsers = userPool
        possibleSecureUsers = resolve_possible_users_security(possibleUsers, TaskName, name)
        available_users = [user for user in possibleSecureUsers if user_resources[user].count < user_resources[user].capacity]
        if available_users == []:
            possibleNormalUsers = resolve_possible_users(possibleUsers, TaskName)
            available_users = [user for user in possibleNormalUsers if user_resources[user].count < user_resources[user].capacity]
        while not available_users:
            yield env.timeout(1)
            available_users = [user for user in possibleNormalUsers if user_resources[user].count < user_resources[user].capacity]
        if available_users:
            userTask = min(available_users, key=lambda u: user_assignments[u])
            user_assignments[userTask] += 1
            if TaskName in security.keys():
                secTasks = security[TaskName]
                for secTask in secTasks.keys():
                    infoSecTask = secTasks[secTask]
                    if infoSecTask[0]:
                        task_users[(secTask, name)].append(userTask)
                    if infoSecTask[1]:
                        task_users[(secTask, name)] = userTask
                    if infoSecTask[2]:
                        if userTask in task_users[(secTask, name, TaskName)]:
                            task_users[(secTask, name, TaskName)][userTask] += 1
                        else:
                            task_users[(secTask, name, TaskName)][userTask] = 1
            request = user_resources[userTask].request()
            yield request
            try:
                time = resolve_task_time('{element.id_bpmn}', {element.maximumTime}, {element.minimumTime}, userTask)
                if env.now < start_standBy:
                    simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="StandBy"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <string key="bpmn:execution" value="{{executionNumber+1}}"/>
            <date key="time:timestamp" value="{{start_standBy}}"/>
            <date key="time:endTime" value="{{env.now}}"/>
            <date key="time:duration" value="{{env.now-start_standBy}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
                simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="{element.bpmn_type}"/>
            <string key="bpmn:name" value="{element.name}"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <string key="bpmn:messageDestiny" value="{element.messageDestiny}"/>
            <string key="bpmn:userTask" value="{{userTask}}"/>
            <int key="bpmn:execution" value="{{executionNumber+1}}"/>
            <int key="bpmn:time" value="{{time}}"/>
            <string key="bpmn:subTask" value="{element.subTask}"/>
            <date key="time:timestamp" value="{{env.now}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
                yield env.timeout(time)
            finally:
                user_resources[userTask].release(request)
                if (TaskName, '{element.messageDestiny}', executionNumber+1, name) not in message_events:
                    message_events.append((TaskName, '{element.messageDestiny}', executionNumber+1, name))
    TaskName = '{element.id_bpmn}'
    if TaskName in requiredData.keys():
        dataObjects = requiredData[TaskName]
        start_standBy_data = env.now
        while not all((dataObject, name) in data for dataObject in dataObjects):
            yield env.timeout(1)
        if env.now < start_standBy_data:
            simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="StandByData"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <date key="time:timestamp" value="{{start_standBy_data}}"/>
            <date key="time:endTime" value="{{env.now}}"/>
            <date key="time:duration" value="{{env.now-start_standBy_data}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
    executionProcesses = []
    for i in range({element.numberOfExecutions}):
        executionProcesses.append(env.process(executeTask(env, TaskName, name, i)))
    yield simpy.AllOf(env, executionProcesses)
    if TaskName in generatedData.keys():
        dataObjects = generatedData[TaskName]
        for dataObject in dataObjects:
            data.append((dataObject, name))
            simulationResults[name].append(
f'''
        <container key="dataObjects">
            <string key="bpmn:id" value="{{dataObject}}"/>
            <string key="bpmn:name" value="{{dataInfo[dataObject]}}"/>
            <date key="time:generationTime" value="{{env.now}}"/>
        </container>''')
    for key, values in gatewayConnections.items():
        if TaskName in values:
            if (key, name) in gatewayOccurrences.keys():
                gatewayOccurrences[(key, name)] += 1
            else:
                gatewayOccurrences[(key, name)] = 1
    return '{element.subTask}'
"""
    elif element.multiInstanceType == None:
        if "Time" in element.loopParameter.keys():
            time = element.loopParameter["Time"]
        else:
            time = 0
        if "Units" in element.loopParameter.keys():
            units = element.loopParameter["Units"]
        else:
            units = -1
        if "Percentage" in element.loopParameter.keys():
            percentage = 1 - element.loopParameter["Percentage"]/100
        else:
            percentage = 1
        functionStr = f"""
def {element.id_bpmn}(env, name):
    TaskName = '{element.id_bpmn}'
    if TaskName in requiredData.keys():
        dataObjects = requiredData[TaskName]
        start_standBy_data = env.now
        while not all((dataObject, name) in data for dataObject in dataObjects):
            yield env.timeout(1)
        if env.now < start_standBy_data:
            simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="StandByData"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <date key="time:timestamp" value="{{start_standBy_data}}"/>
            <date key="time:endTime" value="{{env.now}}"/>
            <date key="time:duration" value="{{env.now-start_standBy_data}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
    units = {units}
    loopStartTime = env.now
    initial = True
    execution = 0
    while ((env.now - loopStartTime < {time}) or ({time}==0)) and (units!=0) and (random.random() < {percentage}) or initial:
        execution = execution + 1
        initial = False
        start_standBy = env.now
        possibleUsers = {element.userTask}
        if possibleUsers is None:
            possibleUsers = userPool
        possibleSecureUsers = resolve_possible_users_security(possibleUsers, TaskName, name)
        available_users = [user for user in possibleSecureUsers if user_resources[user].count < user_resources[user].capacity]
        if available_users == []:
            possibleNormalUsers = resolve_possible_users(possibleUsers, TaskName)
            available_users = [user for user in possibleNormalUsers if user_resources[user].count < user_resources[user].capacity]
        while not available_users:
            yield env.timeout(1)
            available_users = [user for user in possibleNormalUsers if user_resources[user].count < user_resources[user].capacity]
        if available_users:
            userTask = min(available_users, key=lambda u: user_assignments[u])
            user_assignments[userTask] += 1
            if TaskName in security.keys():
                secTasks = security[TaskName]
                for secTask in secTasks.keys():
                    infoSecTask = secTasks[secTask]
                    if infoSecTask[0]:
                        task_users[(secTask, name)].append(userTask)
                    if infoSecTask[1]:
                        task_users[(secTask, name)] = userTask
                    if infoSecTask[2]:
                        if userTask in task_users[(secTask, name, TaskName)]:
                            task_users[(secTask, name, TaskName)][userTask] += 1
                        else:
                            task_users[(secTask, name, TaskName)][userTask] = 1
            request = user_resources[userTask].request()
            yield request
            try:
                time = resolve_task_time('{element.id_bpmn}', {element.maximumTime}, {element.minimumTime}, userTask)
                if env.now < start_standBy:
                    simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="StandBy"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <string key="bpmn:execution" value="{{execution}}"/>
            <date key="time:timestamp" value="{{start_standBy}}"/>
            <date key="time:endTime" value="{{env.now}}"/>
            <date key="time:duration" value="{{env.now-start_standBy}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
                simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="{element.bpmn_type}"/>
            <string key="bpmn:name" value="{element.name}"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <string key="bpmn:messageDestiny" value="{element.messageDestiny}"/>
            <string key="bpmn:userTask" value="{{userTask}}"/>
            <int key="bpmn:execution" value="{{execution}}"/>
            <int key="bpmn:time" value="{{time}}"/>
            <string key="bpmn:subTask" value="{element.subTask}"/>
            <date key="time:timestamp" value="{{env.now}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
                yield env.timeout(time)
            finally:
                user_resources[userTask].release(request)
                if (TaskName, '{element.messageDestiny}', execution, name) not in message_events:
                    message_events.append((TaskName, '{element.messageDestiny}', execution, name))
                units = units - 1
    if TaskName in generatedData.keys():
        dataObjects = generatedData[TaskName]
        for dataObject in dataObjects:
            data.append((dataObject, name))
            simulationResults[name].append(
f'''
        <container key="dataObjects">
            <string key="bpmn:id" value="{{dataObject}}"/>
            <string key="bpmn:name" value="{{dataInfo[dataObject]}}"/>
            <date key="time:generationTime" value="{{env.now}}"/>
        </container>''')
    for key, values in gatewayConnections.items():
        if TaskName in values:
            if (key, name) in gatewayOccurrences.keys():
                gatewayOccurrences[(key, name)] += 1
            else:
                gatewayOccurrences[(key, name)] = 1
    return '{element.subTask}'
"""
    return generateFunction(elements, element.subTask, script + functionStr)


def receiveTask(elements, element, script):
    if element.multiInstanceType == True or (element.multiInstanceType == None and element.loopParameter == None):
        functionStr = f"""
def {element.id_bpmn}(env, name):
    TaskName = '{element.id_bpmn}'
    if TaskName in requiredData.keys():
        dataObjects = requiredData[TaskName]
        start_standBy_data = env.now
        while not all((dataObject, name) in data for dataObject in dataObjects):
            yield env.timeout(1)
        if env.now < start_standBy_data:
            simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="StandByData"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <date key="time:timestamp" value="{{start_standBy_data}}"/>
            <date key="time:endTime" value="{{env.now}}"/>
            <date key="time:duration" value="{{env.now-start_standBy_data}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
    for i in range({element.numberOfExecutions}):
        start_standby_message = env.now
        while not ('{element.messageOrigin}', TaskName, i+1, name) in message_events:
            yield env.timeout(1)
        end_standby_message = env.now
        duration_standby_message = end_standby_message - start_standby_message
        if duration_standby_message < 0:
            simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="StandByMessage"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <string key="bpmn:execution" value="{{i+1}}"/>
            <date key="time:timestamp" value="{{start_standby_message}}"/>
            <date key="time:endTime" value="{{end_standby_message}}"/>
            <date key="time:duration" value="{{duration_standby_message}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
        start_standBy = env.now
        possibleUsers = {element.userTask}
        if possibleUsers is None:
            possibleUsers = userPool
        possibleSecureUsers = resolve_possible_users_security(possibleUsers, TaskName, name)
        available_users = [user for user in possibleSecureUsers if user_resources[user].count < user_resources[user].capacity]
        if available_users == []:
            possibleNormalUsers = resolve_possible_users(possibleUsers, TaskName)
            available_users = [user for user in possibleNormalUsers if user_resources[user].count < user_resources[user].capacity]
        while not available_users:
            yield env.timeout(1)
            available_users = [user for user in possibleNormalUsers if user_resources[user].count < user_resources[user].capacity]
        if available_users:
            userTask = min(available_users, key=lambda u: user_assignments[u])
            user_assignments[userTask] += 1
            if TaskName in security.keys():
                secTasks = security[TaskName]
                for secTask in secTasks.keys():
                    infoSecTask = secTasks[secTask]
                    if infoSecTask[0]:
                        task_users[(secTask, name)].append(userTask)
                    if infoSecTask[1]:
                        task_users[(secTask, name)] = userTask
                    if infoSecTask[2]:
                        if userTask in task_users[(secTask, name, TaskName)]:
                            task_users[(secTask, name, TaskName)][userTask] += 1
                        else:
                            task_users[(secTask, name, TaskName)][userTask] = 1
            request = user_resources[userTask].request()
            yield request
            try:
                time = resolve_task_time('{element.id_bpmn}', {element.maximumTime}, {element.minimumTime}, userTask)
                if env.now < start_standBy:
                    simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="StandBy"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <string key="bpmn:execution" value="{{i+1}}"/>
            <date key="time:timestamp" value="{{start_standBy}}"/>
            <date key="time:endTime" value="{{env.now}}"/>
            <date key="time:duration" value="{{env.now-start_standBy}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
                simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="{element.bpmn_type}"/>
            <string key="bpmn:name" value="{element.name}"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <string key="bpmn:messageOrigin" value="{element.messageOrigin}"/>
            <string key="bpmn:userTask" value="{{userTask}}"/>
            <int key="bpmn:execution" value="{{i+1}}"/>
            <int key="bpmn:time" value="{{time}}"/>
            <string key="bpmn:subTask" value="{element.subTask}"/>
            <date key="time:timestamp" value="{{env.now}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
                yield env.timeout(time)
            finally:
                user_resources[userTask].release(request)
    if TaskName in generatedData.keys():
        dataObjects = generatedData[TaskName]
        for dataObject in dataObjects:
            data.append((dataObject, name))
            simulationResults[name].append(
f'''
        <container key="dataObjects">
            <string key="bpmn:id" value="{{dataObject}}"/>
            <string key="bpmn:name" value="{{dataInfo[dataObject]}}"/>
            <date key="time:generationTime" value="{{env.now}}"/>
        </container>''')
    for key, values in gatewayConnections.items():
        if TaskName in values:
            if (key, name) in gatewayOccurrences.keys():
                gatewayOccurrences[(key, name)] += 1
            else:
                gatewayOccurrences[(key, name)] = 1
    return '{element.subTask}'
"""
    elif element.multiInstanceType == False:
        functionStr = f"""
def {element.id_bpmn}(env, name):
    def executeTask(env, TaskName, name, executionNumber):
        start_standby_message = env.now
        while not ('{element.messageOrigin}', TaskName, executionNumber+1, name) in message_events:
            yield env.timeout(1)
        end_standby_message = env.now
        duration_standby_message = end_standby_message - start_standby_message
        if duration_standby_message < 0:
            simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="StandByMessage"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <string key="bpmn:execution" value="{{executionNumber+1}}"/>
            <date key="time:timestamp" value="{{start_standby_message}}"/>
            <date key="time:endTime" value="{{end_standby_message}}"/>
            <date key="time:duration" value="{{duration_standby_message}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
        start_standBy = env.now
        possibleUsers = {element.userTask}
        if possibleUsers is None:
            possibleUsers = userPool
        possibleSecureUsers = resolve_possible_users_security(possibleUsers, TaskName, name)
        available_users = [user for user in possibleSecureUsers if user_resources[user].count < user_resources[user].capacity]
        if available_users == []:
            possibleNormalUsers = resolve_possible_users(possibleUsers, TaskName)
            available_users = [user for user in possibleNormalUsers if user_resources[user].count < user_resources[user].capacity]
        while not available_users:
            yield env.timeout(1)
            available_users = [user for user in possibleNormalUsers if user_resources[user].count < user_resources[user].capacity]
        if available_users:
            userTask = min(available_users, key=lambda u: user_assignments[u])
            user_assignments[userTask] += 1
            if TaskName in security.keys():
                secTasks = security[TaskName]
                for secTask in secTasks.keys():
                    infoSecTask = secTasks[secTask]
                    if infoSecTask[0]:
                        task_users[(secTask, name)].append(userTask)
                    if infoSecTask[1]:
                        task_users[(secTask, name)] = userTask
                    if infoSecTask[2]:
                        if userTask in task_users[(secTask, name, TaskName)]:
                            task_users[(secTask, name, TaskName)][userTask] += 1
                        else:
                            task_users[(secTask, name, TaskName)][userTask] = 1
            request = user_resources[userTask].request()
            yield request
            try:
                time = resolve_task_time('{element.id_bpmn}', {element.maximumTime}, {element.minimumTime}, userTask)
                if env.now < start_standBy:
                    simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="StandBy"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <string key="bpmn:execution" value="{{executionNumber+1}}"/>
            <date key="time:timestamp" value="{{start_standBy}}"/>
            <date key="time:endTime" value="{{env.now}}"/>
            <date key="time:duration" value="{{env.now-start_standBy}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
                simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="{element.bpmn_type}"/>
            <string key="bpmn:name" value="{element.name}"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <string key="bpmn:messageOrigin" value="{element.messageOrigin}"/>
            <string key="bpmn:userTask" value="{{userTask}}"/>
            <int key="bpmn:execution" value="{{executionNumber+1}}"/>
            <int key="bpmn:time" value="{{time}}"/>
            <string key="bpmn:subTask" value="{element.subTask}"/>
            <date key="time:timestamp" value="{{env.now}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
                yield env.timeout(time)
            finally:
                user_resources[userTask].release(request)
    TaskName = '{element.id_bpmn}'
    if TaskName in requiredData.keys():
        dataObjects = requiredData[TaskName]
        start_standBy_data = env.now
        while not all((dataObject, name) in data for dataObject in dataObjects):
            yield env.timeout(1)
        if env.now < start_standBy_data:
            simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="StandByData"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <date key="time:timestamp" value="{{start_standBy_data}}"/>
            <date key="time:endTime" value="{{env.now}}"/>
            <date key="time:duration" value="{{env.now-start_standBy_data}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
    executionProcesses = []
    for i in range({element.numberOfExecutions}):
        executionProcesses.append(env.process(executeTask(env, TaskName, name, i)))
    yield simpy.AllOf(env, executionProcesses)
    if TaskName in generatedData.keys():
        dataObjects = generatedData[TaskName]
        for dataObject in dataObjects:
            data.append((dataObject, name))
            simulationResults[name].append(
f'''
        <container key="dataObjects">
            <string key="bpmn:id" value="{{dataObject}}"/>
            <string key="bpmn:name" value="{{dataInfo[dataObject]}}"/>
            <date key="time:generationTime" value="{{env.now}}"/>
        </container>''')
    for key, values in gatewayConnections.items():
        if TaskName in values:
            if (key, name) in gatewayOccurrences.keys():
                gatewayOccurrences[(key, name)] += 1
            else:
                gatewayOccurrences[(key, name)] = 1
    return '{element.subTask}'
"""
    elif element.multiInstanceType == None:
        if "Time" in element.loopParameter.keys():
            time = element.loopParameter["Time"]
        else:
            time = 0
        if "Units" in element.loopParameter.keys():
            units = element.loopParameter["Units"]
        else:
            units = -1
        if "Percentage" in element.loopParameter.keys():
            percentage = 1 - element.loopParameter["Percentage"]/100
        else:
            percentage = 1
        functionStr = f"""
def {element.id_bpmn}(env, name):
    TaskName = '{element.id_bpmn}'
    if TaskName in requiredData.keys():
        dataObjects = requiredData[TaskName]
        start_standBy_data = env.now
        while not all((dataObject, name) in data for dataObject in dataObjects):
            yield env.timeout(1)
        if env.now < start_standBy_data:
            simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="StandByData"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <date key="time:timestamp" value="{{start_standBy_data}}"/>
            <date key="time:endTime" value="{{env.now}}"/>
            <date key="time:duration" value="{{env.now-start_standBy_data}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
    units = {units}
    loopStartTime = env.now
    initial = True
    execution = 0
    while ((env.now - loopStartTime < {time}) or ({time}==0)) and (units!=0) and (random.random() < {percentage}) or initial:
        execution = execution + 1
        initial = False
        start_standby_message = env.now
        while not ('{element.messageOrigin}', TaskName, execution, name) in message_events:
            yield env.timeout(1)
        end_standby_message = env.now
        duration_standby_message = end_standby_message - start_standby_message
        if duration_standby_message < 0:
            simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="StandByMessage"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <string key="bpmn:execution" value="{{execution}}"/>
            <date key="time:timestamp" value="{{start_standby_message}}"/>
            <date key="time:endTime" value="{{end_standby_message}}"/>
            <date key="time:duration" value="{{duration_standby_message}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
        start_standBy = env.now
        possibleUsers = {element.userTask}
        if possibleUsers is None:
            possibleUsers = userPool
        possibleSecureUsers = resolve_possible_users_security(possibleUsers, TaskName, name)
        available_users = [user for user in possibleSecureUsers if user_resources[user].count < user_resources[user].capacity]
        if available_users == []:
            possibleNormalUsers = resolve_possible_users(possibleUsers, TaskName)
            available_users = [user for user in possibleNormalUsers if user_resources[user].count < user_resources[user].capacity]
        while not available_users:
            yield env.timeout(1)
            available_users = [user for user in possibleNormalUsers if user_resources[user].count < user_resources[user].capacity]
        if available_users:
            userTask = min(available_users, key=lambda u: user_assignments[u])
            user_assignments[userTask] += 1
            if TaskName in security.keys():
                secTasks = security[TaskName]
                for secTask in secTasks.keys():
                    infoSecTask = secTasks[secTask]
                    if infoSecTask[0]:
                        task_users[(secTask, name)].append(userTask)
                    if infoSecTask[1]:
                        task_users[(secTask, name)] = userTask
                    if infoSecTask[2]:
                        if userTask in task_users[(secTask, name, TaskName)]:
                            task_users[(secTask, name, TaskName)][userTask] += 1
                        else:
                            task_users[(secTask, name, TaskName)][userTask] = 1
            request = user_resources[userTask].request()
            yield request
            try:
                time = resolve_task_time('{element.id_bpmn}', {element.maximumTime}, {element.minimumTime}, userTask)
                if env.now < start_standBy:
                    simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="StandBy"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <string key="bpmn:execution" value="{{execution}}"/>
            <date key="time:timestamp" value="{{start_standBy}}"/>
            <date key="time:endTime" value="{{env.now}}"/>
            <date key="time:duration" value="{{env.now-start_standBy}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
                simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="{element.bpmn_type}"/>
            <string key="bpmn:name" value="{element.name}"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <string key="bpmn:messageOrigin" value="{element.messageOrigin}"/>
            <string key="bpmn:userTask" value="{{userTask}}"/>
            <int key="bpmn:execution" value="{{execution}}"/>
            <int key="bpmn:time" value="{{time}}"/>
            <string key="bpmn:subTask" value="{element.subTask}"/>
            <date key="time:timestamp" value="{{env.now}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
                yield env.timeout(time)
            finally:
                user_resources[userTask].release(request)
                units = units - 1
    if TaskName in generatedData.keys():
        dataObjects = generatedData[TaskName]
        for dataObject in dataObjects:
            data.append((dataObject, name))
            simulationResults[name].append(
f'''
        <container key="dataObjects">
            <string key="bpmn:id" value="{{dataObject}}"/>
            <string key="bpmn:name" value="{{dataInfo[dataObject]}}"/>
            <date key="time:generationTime" value="{{env.now}}"/>
        </container>''')
    for key, values in gatewayConnections.items():
        if TaskName in values:
            if (key, name) in gatewayOccurrences.keys():
                gatewayOccurrences[(key, name)] += 1
            else:
                gatewayOccurrences[(key, name)] = 1
    return '{element.subTask}'
"""
    return generateFunction(elements, element.subTask, script + functionStr)

def intermediateThrowEvent(elements, element, script):
    functionStr = f"""
def {element.id_bpmn}(env, name):
    simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="{element.bpmn_type}"/>
            <string key="bpmn:name" value="{element.name}"/>
            <string key="bpmn:id" value="{element.id_bpmn}"/>
            <string key="bpmn:subTask" value="{element.subTask}"/>
            <date key="time:timestamp" value="{{env.now}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
    yield env.timeout(0)
    return '{element.subTask}'
    """
    return generateFunction(elements, element.subTask, script + functionStr)

def messageIntermediateCatchEvent(elements, element, script):
    functionStr = f"""
def {element.id_bpmn}(env, name):
    TaskName = '{element.id_bpmn}'
    start_standby_message = env.now
    while not ('{element.messageOrigin}', TaskName, name) in message_events:
        yield env.timeout(1)
    end_standby_message = env.now
    duration_standby_message = end_standby_message - start_standby_message
    if duration_standby_message < 0:
        simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="StandByMessage"/>
            <string key="bpmn:id" value="{{TaskName}}"/>
            <string key="bpmn:execution" value="{{execution}}"/>
            <date key="time:timestamp" value="{{start_standby_message}}"/>
            <date key="time:endTime" value="{{end_standby_message}}"/>
            <date key="time:duration" value="{{duration_standby_message}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
    simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="{element.bpmn_type}"/>
            <string key="bpmn:name" value="{element.name}"/>
            <string key="bpmn:id" value="{element.id_bpmn}"/>
            <string key="bpmn:messageOrigin" value="{element.messageOrigin}"/>
            <string key="bpmn:subTask" value="{element.subTask}"/>
            <date key="time:timestamp" value="{{env.now}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
    return '{element.subTask}'
"""
    return generateFunction(elements, element.subTask, script + functionStr)

def messageIntermediateThrowEvent(elements, element, script):
    functionStr = f"""
def {element.id_bpmn}(env, name):
    TaskName = '{element.id_bpmn}'
    simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="{element.bpmn_type}"/>
            <string key="bpmn:name" value="{element.name}"/>
            <string key="bpmn:id" value="{element.id_bpmn}"/>
            <string key="bpmn:messageDestiny" value="{element.messageDestiny}"/>
            <string key="bpmn:subTask" value="{element.subTask}"/>
            <date key="time:timestamp" value="{{env.now}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
    yield env.timeout(0)
    if (TaskName, '{element.messageDestiny}', name) not in message_events:
        message_events.append((TaskName, '{element.messageDestiny}', name))
    return '{element.subTask}'
"""
    return generateFunction(elements, element.subTask, script + functionStr)

def timerIntermediateCatchEvent(elements, element, script):
    functionStr = f"""
def {element.id_bpmn}(env, name):
    simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="{element.bpmn_type}"/>
            <string key="bpmn:name" value="{element.name}"/>
            <string key="bpmn:id" value="{element.id_bpmn}"/>
            <int key="bpmn:time" value="{element.time}"/>
            <string key="bpmn:subTask" value="{element.subTask}"/>
            <date key="time:timestamp" value="{{env.now}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
    yield env.timeout({element.time})
    return '{element.subTask}'
"""
    return generateFunction(elements, element.subTask, script + functionStr)

def endEvent(elements, element, script):
    functionStr = f"""
def {element.id_bpmn}(env, name):
    simulationResults[name].append(
f'''
        <event>
            <string key="bpmn:type" value="{element.bpmn_type}"/>
            <string key="bpmn:name" value="{element.name}"/>
            <string key="bpmn:id" value="{element.id_bpmn}"/>
            <string key="bpmn:subTask" value=""/>
            <date key="time:timestamp" value="{{env.now}}"/>
            <int key="bpmn:instance" value="{{name.split()[-1]}}"/>
        </event>''')
    yield env.timeout(0)
    """
    return script + functionStr

def generateFunction(elements, elementId, script=False):
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
    elif elementType == "BPMNReceiveTask":
        return receiveTask(elements, element, script)
    elif elementType == "BPMNIntermediateThrowEvent":
        return intermediateThrowEvent(elements, element, script)
    elif elementType == "BPMNMessageIntermediateCatchEvent":
        return messageIntermediateCatchEvent(elements, element, script)
    elif elementType == "BPMNMessageIntermediateThrowEvent":
        return messageIntermediateThrowEvent(elements, element, script)
    elif elementType == "BPMNTimerIntermediateCatchEvent":
        return timerIntermediateCatchEvent(elements, element, script)
    elif elementType == "BPMNEndEvent":
        return endEvent(elements, element, script)

def serviceTask(elements):
    securityTasks = set()
    for task in elements['security'].values():
        for st in task.keys():
            securityTasks.add(st)
    script = ""
    for st in securityTasks:
        element = elements[st]
        subtasks_str = ", ".join(element.subTask)
        script = script + f"""
        <event>
            <string key="bpmn:type" value="{element.bpmn_type}"/>
            <string key="bpmn:name" value="{element.name}"/>
            <string key="bpmn:id" value="{element.id_bpmn}"/>
            <boolean key="bpmn:sodSecurity" value="{element.sodSecurity}"/>
            <boolean key="bpmn:bodSecurity" value="{element.bodSecurity}"/>
            <boolean key="bpmn:uocSecurity" value="{element.uocSecurity}"/>
            <int key="bpmn:mth" value="{element.mth}"/>
            <string key="bpmn:subTask" value="{subtasks_str}"/>
        </event>"""
    return script

def generateScript(elements, process, starts, messageStarts, security):
    elementProcess = elements[process]
    if elementProcess.bpmn_type == 'bpmn:Process':
        script = f"""
import simpy
import random

simulationResults = {{}}
nInstances = {elementProcess.instances}
for i in range(nInstances):
    simulationResults[f'Instance {{i+1}}'] = [
f'''
    <trace>
        <string key="concept:name" value="Instance {{i+1}}"/>''']
frequency = {elementProcess.frequency}
rolePool = {elementProcess.userWithRole}
userWithRole = list(set(value for sublist in rolePool.values() for value in sublist))
userWithoutRole = {elementProcess.userWithoutRole}
userPool = userWithRole + userWithoutRole
user_task_count = {{}}
user_assignments = {{user: 0 for user in userPool}}
user_resources = {{}}
message_events = []
task_users = {{}}
security = {elements['security']}
security_events = {{}}
generatedData = {elements['generatedData']}
requiredData = {elements['requiredData']}
dataInfo = {elements['dataInfo']}
defaultData = {elements['defaultData']}
data = []
gatewayConnections = {elements['gatewayConnections']}
for i in range(nInstances):
    for dataObject in defaultData:
        data.append((dataObject, f'Instance {{i + 1}}'))

def resolve_task_time(task_name, max_time, min_time, user):
    if user not in user_task_count:
        user_task_count[user] = {{}}
    if task_name not in user_task_count[user]:
        user_task_count[user][task_name] = 0

    mu = (min_time+max_time)/2
    sigma = (max_time-min_time)/6
    time = max(min_time, min(random.gauss(mu,sigma), max_time))
    reduction_factor = 1 - min(0.05 * user_task_count[user][task_name], 0.5)

    user_task_count[user][task_name] += 1
    return round(time * reduction_factor)

def resolve_possible_users(possibleUsers, taskName):
    users = []
    for item in possibleUsers:
        if item in rolePool:
            users.extend(rolePool[item])
        elif item in userWithoutRole:
            users.append(item)
        elif item in userWithRole:
            users.append(item)
    return list(set(users))

def resolve_possible_users_security(possibleUsers, taskName, instance):
    users = []
    for item in possibleUsers:
        if item in rolePool:
            users.extend(rolePool[item])
        elif item in userWithoutRole:
            users.append(item)
        elif item in userWithRole:
            users.append(item)
    users = list(set(users))
    if taskName in security:
        secTasks = security[taskName]
        for secTask in secTasks.keys():
            infoTask = secTasks[secTask]
            if infoTask[0]:
                if (secTask, instance) in task_users.keys():
                    if isinstance(users, dict):
                        for user in task_users[(secTask, instance)]:
                            users.pop(user) if user in users.keys() else None
                    else:
                        for user in task_users[(secTask, instance)]:
                            users.remove(user) if user in users else None
                else:
                    task_users[(secTask, instance)] = []
            elif infoTask[1]:
                if (secTask, instance) in task_users.keys():
                    if isinstance(users, dict):
                        n = users[task_users[(secTask, instance)]]
                        users.clear()
                        users[task_users[(secTask, instance)]] = n
                    else:
                        if task_users[(secTask, instance)] in users:
                            users = [task_users[(secTask, instance)]]
                        else:
                            users = []
            elif infoTask[2]:
                if (secTask, instance, taskName) in task_users.keys():
                    for user in task_users[(secTask, instance, taskName)].keys():
                        if task_users[(secTask, instance, taskName)][user] >= infoTask[3]:
                            users.pop(user)
    return users
"""
        startElements = {}
        messageStartElements = {}
        for start in starts:
            startEvent = elements[start]
            startElements[start] = [startEvent.bpmn_type, startEvent.name, startEvent.id_bpmn, startEvent.subTask]
            script = generateFunction(elements, startEvent.subTask, script)
        for start in messageStarts:
            startEvent = elements[start]
            messageStartElements[start] = [startEvent.bpmn_type, startEvent.name, startEvent.id_bpmn, startEvent.messageOrigin, startEvent.subTask]
            script = generateFunction(elements, startEvent.subTask, script)
        scriptMainFunction = f"""
def process_task(env, name, task_name):
    task_func = globals()[task_name]
    result = yield env.process(task_func(env, name))
    if result:
        if isinstance(result, list):
            for next_task in result:
                if next_task in gatewayConnections.keys():
                    if (next_task, name) in gatewayOccurrences.keys() and gatewayOccurrences[(next_task, name)] == len(gatewayConnections[next_task]):
                        if (next_task, name) not in gatewayProcessed:
                            gatewayProcessed.add((next_task, name))
                            env.process(process_task(env, name, next_task))
                else:
                    env.process(process_task(env, name, next_task))
        else:
            if result in gatewayConnections.keys():
                if (result, name) in gatewayOccurrences.keys() and gatewayOccurrences[(result, name)] == len(gatewayConnections[result]):
                    if (result, name) not in gatewayProcessed:
                        gatewayProcessed.add((result, name))
                        env.process(process_task(env, name, result))
            else:
                env.process(process_task(env, name, result))


def start_process(env, name, nextTask):
    yield env.process(process_task(env, name, nextTask))

def main(env):
    global user_resources
    user_resources = {{user: simpy.Resource(env, capacity=1) for user in userPool}}
    simulationResults['Start'] = f'''<?xml version="1.0" encoding="UTF-8"?>
<log xes.version="1.0" xes.features="nested-attributes" openxes.version="1.0RC7" xmlns="http://www.xes-standard.org/">
    <classifier name="Activity (by BPMN ID)" keys="bpmn:id" scope="event"/>
    <global>
        <string key="type" value="{elementProcess.bpmn_type}"/>
        <string key="name" value="{elementProcess.name}"/>
        <string key="id_bpmn" value="{elementProcess.id_bpmn}"/>
        <int key="instances" value="{{nInstances}}"/>
        <int key="frequency" value="{{frequency}}"/>
        <list key="userWithoutRole">
            <values>"""
        if elementProcess.bpmn_type == "bpmn:Process":
            scriptMainFunction = scriptMainFunction + """
        <list key="userWithoutRole">
            <values>"""
            for user in elementProcess.userWithoutRole:
                scriptMainFunction = scriptMainFunction + f"""
                <string value="{user}"/>"""
            scriptMainFunction = scriptMainFunction + f"""
            </values>
        </list>
        <container key="userWithRole">"""
            for role, users in elementProcess.userWithRole.items():
                scriptMainFunction = scriptMainFunction + f"""
            <list key="{role}">"""
                for user in users:
                    scriptMainFunction = scriptMainFunction + f"""
                <values>
                    <string value="{user}"/>
                </values>"""
                scriptMainFunction = scriptMainFunction + f"""
            <list>"""
        scriptMainFunction = scriptMainFunction + f"""
    </global>'''
    startEvents = {startElements}
    messageStartEvents = {messageStartElements}
    for i in range(nInstances):
        for start in {starts}:
            simulationResults[f'Instance {{i+1}}'].append(
f'''
        <event>
            <string key="bpmn:type" value="{{startEvents[start][0]}}"/>
            <string key="bpmn:name" value="{{startEvents[start][1]}}"/>
            <string key="bpmn:id" value="{{startEvents[start][2]}}"/>
            <string key="bpmn:subTask" value="{{startEvents[start][3]}}"/>
            <date key="time:timestamp" value="{{env.now}}"/>
            <int key="bpmn:instance" value="{{i+1}}"/>
        </event>''')
            env.process(start_process(env, f'Instance {{i + 1}}', startEvents[start][3]))
        for start in {messageStarts}:
            start_standby_message = env.now
            while (messageStartEvents[start][3], start, f'Instance {{i + 1}}') not in message_events:
                yield env.timeout(1)
            end_standby_message = env.now
            duration_standby_message = end_standby_message - start_standby_message
            if duration_standby_message < 0:
                simulationResults[f'Instance {{i+1}}'].append(
f'''
        <event>
            <string key="bpmn:type" value="StandByMessage"/>
            <string key="bpmn:id" value="{{start}}"/>
            <date key="time:timestamp" value="{{start_standby_message}}"/>
            <date key="time:endTime" value="{{end_standby_message}}"/>
            <date key="time:duration" value="{{duration_standby_message}}"/>
            <int key="bpmn:instance" value="{{i+1}}"/>
        </event>''')
            simulationResults[f'Instance {{i+1}}'].append(
f'''
        <event>
            <string key="bpmn:type" value="{{messageStartEvents[start][0]}}"/>
            <string key="bpmn:name" value="{{messageStartEvents[start][1]}}"/>
            <string key="bpmn:id" value="{{messageStartEvents[start][2]}}"/>
            <string key="bpmn:messageOrigin" value="{{messageStartEvents[start][3]}}"/>
            <string key="bpmn:subTask" value="{{messageStartEvents[start][4]}}"/>
            <date key="time:timestamp" value="{{env.now}}"/>
            <int key="bpmn:instance" value="{{i+1}}"/>
        </event>''')
            env.process(start_process(env, f'Instance {{i + 1}}', messageStartEvents[start][4]))
        yield env.timeout(frequency)

env = simpy.Environment()
env.process(main(env))
env.run()
res = simulationResults['Start']
simulationResults.pop('Start')
for key in sorted(simulationResults):
    for str in simulationResults[key]:
        res = res + str
    res = res + '''{serviceTask(elements)}
    </trace>'''
res = res + '''
</log>'''
with open(f'files/resultSimulation.xes', 'w') as f:
    f.write(res)"""
    else:
        script = f"""
import simpy
import random

simulationResults = {{}}
nInstances = {elementProcess.instances}
for i in range(nInstances):
    simulationResults[f'Instance {{i+1}}'] = [
f'''
    <trace>
        <string key="concept:name" value="Instance {{i+1}}"/>''']
usersPerLane = {elements['users']}
userPool = []
for u in usersPerLane.values():
    userPool.extend(u)
userPool = list(set(userPool))
elementsContainer = {elements['elementsContainer']}
user_task_count = {{}}
user_assignments = {{user: 0 for user in userPool}}
user_resources = {{}}
message_events = []
task_users = {{}}
security = {elements['security']}
security_events = {{}}
generatedData = {elements['generatedData']}
requiredData = {elements['requiredData']}
dataInfo = {elements['dataInfo']}
defaultData = {elements['defaultData']}
gatewayConnections = {elements['gatewayConnections']}
gatewayOccurrences = {{}}
gatewayProcessed = set()
data = []
for i in range(nInstances):
    for dataObject in defaultData:
        data.append((dataObject, f'Instance {{i + 1}}'))

def resolve_task_time(task_name, max_time, min_time, user):
    if user not in user_task_count:
        user_task_count[user] = {{}}
    if task_name not in user_task_count[user]:
        user_task_count[user][task_name] = 0

    mu = (min_time+max_time)/2
    sigma = (max_time-min_time)/6
    time = max(min_time, min(random.gauss(mu,sigma), max_time))
    reduction_factor = 1 - min(0.05 * user_task_count[user][task_name], 0.5)

    user_task_count[user][task_name] += 1
    return round(time * reduction_factor)

def resolve_possible_users(possibleUsers, taskName):
    laneUsers = usersPerLane[elementsContainer[taskName]]
    users = []
    for item in possibleUsers:
        if item in laneUsers:
            users.append(item)
    return list(set(users))

def resolve_possible_users_security(possibleUsers, taskName, instance):
    laneUsers = usersPerLane[elementsContainer[taskName]]
    users = []
    for item in possibleUsers:
        if item in laneUsers:
            users.append(item)
    users = list(set(users))
    if taskName in security:
        secTasks = security[taskName]
        for secTask in secTasks.keys():
            infoTask = secTasks[secTask]
            if infoTask[0]:
                if (secTask, instance) in task_users.keys():
                    if isinstance(users, dict):
                        for user in task_users[(secTask, instance)]:
                            users.pop(user) if user in users.keys() else None
                    else:
                        for user in task_users[(secTask, instance)]:
                            users.remove(user) if user in users else None
                else:
                    task_users[(secTask, instance)] = []
            elif infoTask[1]:
                if (secTask, instance) in task_users.keys():
                    if isinstance(users, dict):
                        n = users[task_users[(secTask, instance)]]
                        users.clear()
                        users[task_users[(secTask, instance)]] = n
                    else:
                        if task_users[(secTask, instance)] in users:
                            users = [task_users[(secTask, instance)]]
                        else:
                            users = []
            elif infoTask[2]:
                if (secTask, instance, taskName) in task_users.keys():
                    for user in task_users[(secTask, instance, taskName)].keys():
                        if task_users[(secTask, instance, taskName)][user] >= infoTask[3]:
                            users.remove(user)
                else:
                    task_users[(secTask, instance, taskName)] = {{}}
                    for user in users:
                        task_users[(secTask, instance, taskName)][user] = 0
    return users
"""
        startElements = {}
        messageStartElements = {}
        for start in starts:
            startEvent = elements[start]
            startElements[start] = [startEvent.bpmn_type, startEvent.name, startEvent.id_bpmn, startEvent.subTask]
            script = generateFunction(elements, startEvent.subTask, script)
        for start in messageStarts:
            startEvent = elements[start]
            messageStartElements[start] = [startEvent.bpmn_type, startEvent.name, startEvent.id_bpmn, startEvent.messageOrigin, startEvent.subTask]
            script = generateFunction(elements, startEvent.subTask, script)
        laneString = ''
        
        lanes = elements['lanes']
        for laneName in lanes:
            lane = elements[laneName]
            laneString = laneString + f'''
        <container key="{lane.bpmn_type}">
            <string key="bpmn:name" value="{lane.name}"/>
            <string key="bpmn:id" value="{lane.id_bpmn}"/>
            <string key="bpmn:users" value="{lane.users}"/>
            <string key="bpmn:elements" value="{lane.contained_elements}"/>
        </container>'''
        scriptMainFunction = f"""
def process_task(env, name, task_name):
    task_func = globals()[task_name]
    result = yield env.process(task_func(env, name))
    if result:
        if isinstance(result, list):
            for next_task in result:
                if next_task in gatewayConnections.keys():
                    if (next_task, name) in gatewayOccurrences.keys() and gatewayOccurrences[(next_task, name)] == len(gatewayConnections[next_task]):
                        if (next_task, name) not in gatewayProcessed:
                            gatewayProcessed.add((next_task, name))
                            env.process(process_task(env, name, next_task))
                else:
                    env.process(process_task(env, name, next_task))
        else:
            if result in gatewayConnections.keys():
                if (result, name) in gatewayOccurrences.keys() and gatewayOccurrences[(result, name)] == len(gatewayConnections[result]):
                    if (result, name) not in gatewayProcessed:
                        gatewayProcessed.add((result, name))
                        env.process(process_task(env, name, result))
            else:
                env.process(process_task(env, name, result))


def start_process(env, name, nextTask):
    yield env.process(process_task(env, name, nextTask))

def participant_process(env, frequency, p):
    startEvents = {startElements}
    messageStartEvents = {messageStartElements}
    startsParticipant = {elements['startsParticipant']}
    for i in range(nInstances):
        for start in {starts}:
            if startsParticipant[start] == p:
                simulationResults[f'Instance {{i+1}}'].append(
f'''
        <event>
            <string key="bpmn:type" value="{{startEvents[start][0]}}"/>
            <string key="bpmn:name" value="{{startEvents[start][1]}}"/>
            <string key="bpmn:id" value="{{startEvents[start][2]}}"/>
            <string key="bpmn:subTask" value="{{startEvents[start][3]}}"/>
            <date key="time:timestamp" value="{{env.now}}"/>
            <int key="bpmn:instance" value="{{i+1}}"/>
        </event>''')
                env.process(start_process(env, f'Instance {{i + 1}}', startEvents[start][3]))
        for start in {messageStarts}:
            if startsParticipant[start] == p:
                start_standby_message = env.now
                while (messageStartEvents[start][3], start, f'Instance {{i + 1}}') not in message_events:
                    yield env.timeout(1)
                end_standby_message = env.now
                duration_standby_message = end_standby_message - start_standby_message
                if duration_standby_message < 0:
                    simulationResults[f'Instance {{i+1}}'].append(
f'''
        <event>
            <string key="bpmn:type" value="StandByMessage"/>
            <string key="bpmn:id" value="{{start}}"/>
            <date key="time:timestamp" value="{{start_standby_message}}"/>
            <date key="time:endTime" value="{{end_standby_message}}"/>
            <date key="time:duration" value="{{duration_standby_message}}"/>
            <int key="bpmn:instance" value="{{i+1}}"/>
        </event>''')
            simulationResults[f'Instance {{i+1}}'].append(
f'''
        <event>
            <string key="bpmn:type" value="{{messageStartEvents[start][0]}}"/>
            <string key="bpmn:name" value="{{messageStartEvents[start][1]}}"/>
            <string key="bpmn:id" value="{{messageStartEvents[start][2]}}"/>
            <string key="bpmn:messageOrigin" value="{{messageStartEvents[start][3]}}"/>
            <string key="bpmn:subTask" value="{{messageStartEvents[start][4]}}"/>
            <date key="time:timestamp" value="{{env.now}}"/>
            <int key="bpmn:instance" value="{{i+1}}"/>
        </event>''')
            env.process(start_process(env, f'Instance {{i + 1}}', messageStartEvents[start][4]))
        yield env.timeout(frequency)

def main(env):
    global user_resources
    user_resources = {{user: simpy.Resource(env, capacity=1) for user in userPool}}
    simulationResults['Start'] = f'''<?xml version="1.0" encoding="UTF-8"?>
<log xes.version="1.0" xes.features="nested-attributes" openxes.version="1.0RC7" xmlns="http://www.xes-standard.org/">
    <classifier name="Activity (by BPMN ID)" keys="bpmn:id" scope="event"/>
    <global>
        <string key="type" value="{elementProcess.bpmn_type}"/>
        <string key="name" value="{elementProcess.name}"/>
        <string key="id_bpmn" value="{elementProcess.id_bpmn}"/>
        <int key="instances" value="{{nInstances}}"/>"/>
        """
        if elementProcess.bpmn_type == "bpmn:Process":
            scriptMainFunction = scriptMainFunction + """
        <list key="userWithoutRole">
            <values>"""
            for user in elementProcess.userWithoutRole:
                scriptMainFunction = scriptMainFunction + f"""
                <string value="{user}"/>"""
            scriptMainFunction = scriptMainFunction + f"""
            </values>
        </list>
        <container key="userWithRole">"""
            for role, users in elementProcess.userWithRole.items():
                scriptMainFunction = scriptMainFunction + f"""
            <list key="{role}">"""
                for user in users:
                    scriptMainFunction = scriptMainFunction + f"""
                <values>
                    <string value="{user}"/>
                </values>"""
                scriptMainFunction = scriptMainFunction + f"""
            <list>"""
        scriptMainFunction = scriptMainFunction + laneString + f"""
    </global>'''
    for frequency, p in {elements['participants']}:
        env.process(participant_process(env, frequency, p))
        yield env.timeout(0)

env = simpy.Environment()
env.process(main(env))
env.run()
res = simulationResults['Start']
simulationResults.pop('Start')
for key in sorted(simulationResults):
    for str in simulationResults[key]:
        res = res + str
    res = res + '''{serviceTask(elements)}
    </trace>'''
res = res + '''
</log>'''
with open(f'files/resultSimulation.xes', 'w') as f:
    f.write(res)"""
    return script + scriptMainFunction, process
