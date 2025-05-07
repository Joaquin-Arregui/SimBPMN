def intermediateThrowEvent(elements, element, script):
    from simulator.simulationFunctions.generateFunction import generateFunction
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
    from simulator.simulationFunctions.generateFunction import generateFunction
    functionStr = f"""
def {element.id_bpmn}(env, name):
    TaskName = '{element.id_bpmn}'
    start_standby_message = env.now
    while not ('{element.messageOrigin}', TaskName, 1, name) in message_events:
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
    from simulator.simulationFunctions.generateFunction import generateFunction
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
    if (TaskName, '{element.messageDestiny}', 1, name) not in message_events:
        message_events.append((TaskName, '{element.messageDestiny}', 1, name))
    return '{element.subTask}'
    """
    return generateFunction(elements, element.subTask, script + functionStr)

def timerIntermediateCatchEvent(elements, element, script):
    from simulator.simulationFunctions.generateFunction import generateFunction
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
    from simulator.simulationFunctions.generateFunction import generateFunction
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