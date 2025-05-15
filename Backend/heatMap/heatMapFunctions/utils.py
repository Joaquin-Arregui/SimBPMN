import os
import xml.etree.ElementTree as ET

def strip_default_namespace(elem):
    if elem.tag.startswith('{'):
        elem.tag = elem.tag.split('}', 1)[1]
    for child in elem:
        strip_default_namespace(child)

def normalize_time_dict(time_dict):
    non_zero_values = [v for v in time_dict.values() if v > 0]
    if not non_zero_values:
        return {k: 0 for k in time_dict}
    max_val = max(non_zero_values)
    min_val = min(non_zero_values)
    if max_val == min_val:
        return {k: (1 if v == max_val else 0) for k, v in time_dict.items()}
    norm_dict = {}
    for k, v in time_dict.items():
        if v == 0:
            norm_dict[k] = 0
        else:
            norm_dict[k] = 0.1 + 0.9 * (v - min_val) / (max_val - min_val)
    return norm_dict

def getTotalTime():
    ns = {'xes': 'http://www.xes-standard.org/'}
    scriptDir = os.path.dirname(__file__)
    resultsFile = os.path.join(os.path.dirname(scriptDir), 'files', f'resultSimulation.xes')
    tree = ET.parse(resultsFile)
    root = tree.getroot()
    min_tstamp = float('inf')
    max_tstamp = float('-inf')
    for date_tag in root.findall('.//xes:date', ns):
        if date_tag.get('key') == 'time:timestamp':
            t = int(date_tag.get('value'))
            if t < min_tstamp:
                min_tstamp = t
            if t > max_tstamp:
                max_tstamp = t
    total_time = max_tstamp - min_tstamp
    return total_time

def merge_intervals(intervals):
    if not intervals:
        return []
    sorted_intervals = sorted(intervals, key=lambda x: x[0])
    merged = []
    current_start, current_end = sorted_intervals[0]
    for start, end in sorted_intervals[1:]:
        if start <= current_end:
            current_end = max(current_end, end)
        else:
            merged.append((current_start, current_end))
            current_start, current_end = start, end
    merged.append((current_start, current_end))
    return merged


def calculate_task_duration(intervals):
    merged_intervals = merge_intervals(intervals)
    return sum(end - start for start, end in merged_intervals)


def calculate_total_durations(tasks_dict):
    return {
        task_id: calculate_task_duration(intervals)
        for task_id, intervals in tasks_dict.items()
    }