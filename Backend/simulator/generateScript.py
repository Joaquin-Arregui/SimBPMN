from simulator.simulationFunctions.generateFunction import generateFunction

def generateScript(elements, process, starts, messageStarts):
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
generatedData = {elements['generatedData']}
requiredData = {elements['requiredData']}
dataInfo = {elements['dataInfo']}
defaultData = {elements['defaultData']}
data = []
gatewayConnections = {elements['gatewayConnections']}
gatewayOccurrences = {{}}
gatewayProcessed = set()
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
        <int key="frequency" value="{{frequency}}"/>"""
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
        </container>
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
    res = res + '''
    </trace>'''
res = res + '''
</log>'''
with open(f'heatMap/files/resultSimulation.xes', 'w') as f:
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
generatedData = {elements['generatedData']}
requiredData = {elements['requiredData']}
dataInfo = {elements['dataInfo']}
defaultData = {elements['defaultData']}
data = []
gatewayOccurrences = {{}}
gatewayProcessed = set()
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
    laneUsers = usersPerLane[elementsContainer[taskName]]
    users = []
    for item in possibleUsers:
        if item in laneUsers:
            users.append(item)
    return list(set(users))

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
                while (messageStartEvents[start][3], start, 1, f'Instance {{i + 1}}') not in message_events:
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
        <int key="instances" value="{{nInstances}}"/>"""
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
    res = res + '''
    </trace>'''
res = res + '''
</log>'''
with open(f'heatMap/files/resultSimulation.xes', 'w') as f:
    f.write(res)"""
    return script + scriptMainFunction, process
