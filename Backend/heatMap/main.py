from heatMap.heatMapFunctions.getColorDict import getColorDict

def getHeatMap(diagram):
    elementColorDict = getColorDict()
    for element, color in elementColorDict.items():
        oldString = f'bpmnElement="{element}"'
        newString = f'bpmnElement="{element}" bioc:fill="{color}"'
        diagram = diagram.replace(oldString, newString)
    return diagram
