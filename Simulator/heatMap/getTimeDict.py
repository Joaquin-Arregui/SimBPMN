import xml.etree.ElementTree as ET
import os

def strip_default_namespace(elem):
    if elem.tag.startswith('{'):
        elem.tag = elem.tag.split('}', 1)[1]
    for child in elem:
        strip_default_namespace(child)

def getTimeDict():
    scriptDir = os.path.dirname(__file__)
    resultsFile = os.path.join(os.path.dirname(scriptDir), 'files', f'resultSimulation.xes')
    tree = ET.parse(resultsFile)
    root = tree.getroot()
    strip_default_namespace(root)
    time_dict = {}

    for trace in root.findall('trace'):
        tasks_info = {}

        for event in trace.findall('event'):
            bpmn_id = None
            start_timestamp = None
            duration = 0
            for string_tag in event.findall('string'):
                if string_tag.get('key') == 'bpmn:id':
                    bpmn_id = string_tag.get('value')
            for date_tag in event.findall('date'):
                if date_tag.get('key') == 'time:timestamp':
                    start_timestamp = int(date_tag.get('value'))
            for int_tag in event.findall('int'):
                if int_tag.get('key') == 'bpmn:time':
                    duration = int(int_tag.get('value'))
            if bpmn_id is not None and start_timestamp is not None:
                end_timestamp = start_timestamp + duration
                if bpmn_id not in tasks_info:
                    tasks_info[bpmn_id] = {
                        "start": start_timestamp,
                        "end": end_timestamp
                    }
                else:
                    if start_timestamp < tasks_info[bpmn_id]["start"]:
                        tasks_info[bpmn_id]["start"] = start_timestamp
                    if end_timestamp > tasks_info[bpmn_id]["end"]:
                        tasks_info[bpmn_id]["end"] = end_timestamp
        for task, times in tasks_info.items():
            if task in time_dict.keys():
                time_dict[task] = time_dict[task] + (times['end'] - times['start'])
            else:
                time_dict[task] = (times['end'] - times['start'])
    return time_dict
