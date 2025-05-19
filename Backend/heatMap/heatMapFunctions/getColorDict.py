from heatMap.heatMapFunctions.getTimeDict import getTimeDict


def getColor(value):
    if value <= 0:
        return "#00CC00"
    elif value >= 1:
        return "#CC0000"
    start_color = (255, 255, 0)
    end_color = (255, 0, 0)
    red = int(start_color[0] + (end_color[0] - start_color[0]) * value)
    green = int(start_color[1] + (end_color[1] - start_color[1]) * value)
    blue = 0
    hex_color = f"#{red:02X}{green:02X}{blue:02X}"
    return hex_color

def getColorDict():
    elementTimeDict = getTimeDict()
    elementColorDict = {}
    for element, time in elementTimeDict.items():
        elementColorDict[element] = getColor(time)
    return elementColorDict