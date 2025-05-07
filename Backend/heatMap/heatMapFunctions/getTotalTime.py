import os
import xml.etree.ElementTree as ET

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
