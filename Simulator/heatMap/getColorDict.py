from heatMap.getTimeDict import getTimeDict
from heatMap.getTotalTime import getTotalTime


def getColor(value):
    totalTime = getTotalTime()
    if value <= 0:
        return "#00CC00"
    elif value >= totalTime:
        return "#CC0000"
    normalized_value = value / totalTime
    start_color = (255, 255, 0)
    end_color = (255, 0, 0)
    red = int(start_color[0] + (end_color[0] - start_color[0]) * normalized_value)
    green = int(start_color[1] + (end_color[1] - start_color[1]) * normalized_value)
    blue = int(start_color[2] + (end_color[2] - start_color[2]) * normalized_value)
    hex_color = f"#{red:02X}{green:02X}{blue:02X}"
    return hex_color

def getColorDict():
    elementTimeDict = getTimeDict()
    elementColorDict = {}
    for element, time in elementTimeDict.items():
        elementColorDict[element] = getColor(time)
    return elementColorDict