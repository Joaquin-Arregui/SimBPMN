package com.cor.cep.util;

import com.cor.cep.event.Task;
import com.cor.cep.handler.TaskEventHandler;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;
import java.util.stream.Collectors;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.*;

import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

@Component
public class TaskProcessor {

    private static final Logger LOG = LoggerFactory.getLogger(TaskProcessor.class);

    @Autowired
    private TaskEventHandler taskEventHandler;

    public List<Task> parseXESFile(String filePath) {
    List<Task> tasks = new ArrayList<>();

    try {
        File file = new File(filePath);
        DocumentBuilderFactory dbFactory = DocumentBuilderFactory.newInstance();
        DocumentBuilder dBuilder = dbFactory.newDocumentBuilder();
        Document doc = dBuilder.parse(file);

        doc.getDocumentElement().normalize();

        NodeList traceList = doc.getElementsByTagName("trace");
        for (int i = 0; i < traceList.getLength(); i++) {
            Node traceNode = traceList.item(i);
            if (traceNode.getNodeType() == Node.ELEMENT_NODE) {
                Element traceElement = (Element) traceNode;

                String instanceName = null;
                NodeList traceChildren = traceElement.getElementsByTagName("string");
                for (int j = 0; j < traceChildren.getLength(); j++) {
                    Element strEl = (Element) traceChildren.item(j);
                    if ("concept:name".equals(strEl.getAttribute("key"))) {
                        instanceName = strEl.getAttribute("value"); // Ej "Instance_1", "Instance_2"
                        break;
                    }
                }

                Integer instanceNumber = extractInstanceNumber(instanceName);

                NodeList eventList = traceElement.getElementsByTagName("event");
                for (int k = 0; k < eventList.getLength(); k++) {
                    Node eventNode = eventList.item(k);
                    if (eventNode.getNodeType() == Node.ELEMENT_NODE) {
                        Element eventElement = (Element) eventNode;
                        Task task = parseXesEvent(eventElement, instanceNumber);
                        if (task != null) {
                            tasks.add(task);
                        }
                    }
                }
            }
        }
    } catch (Exception e) {
        LOG.error("Error reading/parsing XES file: {}", filePath, e);
    }

    return tasks;
}

private Integer extractInstanceNumber(String instanceName) {
    if (instanceName == null) return null;

    String digits = instanceName.replaceAll("\\D+", "");
    try {
        return Integer.parseInt(digits);
    } catch (NumberFormatException e) {
        return null;
    }
}

private Task parseXesEvent(Element eventElement, Integer instance) {
    // Campos a rellenar
    String type = "Task"; 
    String idBpmn = null;
    String userTask = null;
    List<String> subTasks = new ArrayList<>();
    boolean sodSecurity = false, bodSecurity = false, uocSecurity = false;
    Integer mth = null, execution = null;
    Long startTime = null, stopTime = null, time = null; 
    String name = "Unnamed";

    // Recorremos hijos <string>, <int>, <boolean>, <date>, etc. 
    NodeList childAttributes = eventElement.getChildNodes();
    for (int i = 0; i < childAttributes.getLength(); i++) {
        Node node = childAttributes.item(i);
        if (node.getNodeType() == Node.ELEMENT_NODE) {
            Element attr = (Element) node;

            // key="..." value="..."
            String key = attr.getAttribute("key");
            String strValue = attr.getAttribute("value");

            // También podrías verificar el tag <boolean>, <int>, <date> para parsear distinto
            // en lugar de fiarte sólo de "key" y "value". Ej.: if (attr.getTagName().equals("int")) ...
            
            switch (key) {
                case "bpmn:type":
                    // Mapeamos a un tipo BPMN según la convención de tu ejemplo
                    type = mapToBpmnType(strValue); 
                    break;
                case "bpmn:id":
                    idBpmn = strValue;
                    break;
                case "bpmn:userTask":
                    userTask = strValue;
                    break;
                    case "bpmn:subTask":
                    if (!strValue.trim().isEmpty()) {
                        subTasks = Arrays.asList(strValue.split("\\s*,\\s*"));
                    }
                    break;                
                case "bpmn:sodSecurity":
                    sodSecurity = Boolean.parseBoolean(strValue);
                    break;
                case "bpmn:bodSecurity":
                    bodSecurity = Boolean.parseBoolean(strValue);
                    break;
                case "bpmn:uocSecurity":
                    uocSecurity = Boolean.parseBoolean(strValue);
                    break;
                case "bpmn:mth":
                    mth = parseInteger(strValue);
                    break;
                case "bpmn:time":
                    time = parseLong(strValue);
                    break;
                case "bpmn:execution":
                    execution = parseInteger(strValue);
                    break;
                case "bpmn:instance":
                    instance = parseInteger(strValue);
                    break;
                case "time:timestamp":
                    startTime = parseLong(strValue);
                    break;
                default:
                    break;
            }
        }
    }

    Task task = new Task(
        type, 
        name, 
        idBpmn, 
        mth, 
        subTasks, 
        userTask, 
        bodSecurity, 
        sodSecurity, 
        uocSecurity,
        startTime,
        stopTime,
        time,
        instance, 
        1,
        execution != null ? execution : 0,
        null
    );

    return task;
}

private Integer parseInteger(String val) {
    try {
        return Integer.valueOf(val);
    } catch (NumberFormatException e) {
        return null;
    }
}

private Long parseLong(String val) {
    try {
        return Long.valueOf(val);
    } catch (NumberFormatException e) {
        return null;
    }
}

private String mapToBpmnType(String conceptName) {
    switch (conceptName) {
        case "StartEvent":
            return "bpmn:StartEvent";
        case "Task":
            return "bpmn:Task";
        case "ServiceTask":
            return "bpmn:ServiceTask";
        case "ExclusiveGateway":
            return "bpmn:ExclusiveGateway";
        case "EndEvent":
            return "bpmn:EndEvent";
        default:
            return "bpmn:Task"; 
    }
}

public String generateSimulationFormat(List<Task> tasks) {

    StringBuilder sb = new StringBuilder();
    int totalInstances = tasks.stream()
        .filter(t -> t.getInstance() != null)
        .map(Task::getInstance)
        .collect(Collectors.toSet()).size();

    List<String> uniqueUsers = tasks.stream()
        .map(Task::getUserTask)
        .filter(Objects::nonNull)
        .distinct()
        .collect(Collectors.toList());

    sb.append("Element: [type=bpmn:Process, name=Unnamed, id_bpmn=Process_1, ")
      .append("instances=").append(totalInstances).append(", ")
      .append("frequency=30, ")
      .append("userWithoutRole=").append(uniqueUsers.toString()).append(", ")
      .append("userWithRole={}]\n");

    for (Task t : tasks) {
        Integer inst = (t.getInstance() != null) ? t.getInstance() : -1;
        sb.append("Instance ")
          .append(inst)
          .append(": [");

        sb.append("type=").append(t.getType()).append(", ");
        sb.append("name=").append(t.getName()).append(", ");
        sb.append("id_bpmn=").append(t.getIdBpmn()).append(", ");

        if (t.getUserTask() != null) {
            sb.append("userTask=").append(t.getUserTask()).append(", ");
        }
        if (t.getExecution() != null && t.getExecution() != 0) {
            sb.append("execution=").append(t.getExecution()).append(", ");
        }
        if (t.getTime() != null) {
            sb.append("time=").append(t.getTime()).append(", ");
        }
        String subTaskStr = String.join(", ", t.getSubTasks());
        sb.append("subTask=\"").append(subTaskStr).append("\", ");

        if (t.getStartTime() != null) {
            sb.append("startTime=").append(t.getStartTime()).append(", ");
        }

        if (t.isSodSecurity()) {
            sb.append("sodSecurity=True, ");
        }
        if (t.isBodSecurity()) {
            sb.append("bodSecurity=True, ");
        }
        if (t.isUocSecurity()) {
            sb.append("uocSecurity=True, ");
        }
        if (t.getMth() != null) {
            sb.append("mth=").append(t.getMth()).append(", ");
        }
        sb.append("instance=").append(inst).append("]\n");
    }

    return sb.toString();
}

public void processXESFiles(String directoryPath) {
    File folder = new File(directoryPath);
    File[] listOfFiles = folder.listFiles((dir, name) -> name.toLowerCase().endsWith(".xes"));

    if (listOfFiles != null) {
        for (File file : listOfFiles) {
            if (file.isFile()) {
                LOG.info("Processing XES file: {}", file.getAbsolutePath());

                try {
                    List<Task> tasks = parseXESFile(file.getAbsolutePath());
                    tasks.forEach(taskEventHandler::handle);

                    LOG.info("Successfully processed XES file: {}", file.getName());
                } catch (Exception e) {
                    LOG.error("Error reading/parsing XES file: {}", file.getName(), e);
                }
            }
        }
    } else {
        LOG.error("No XES files found in the directory: {}", directoryPath);
    }

    taskEventHandler.writeViolationsToFile("../Modeler/example/src/files/violations.txt");
}


    public void processTaskFiles(String directoryPath) {
        File folder = new File(directoryPath);
        File[] listOfFiles = folder.listFiles((dir, name) -> name.toLowerCase().endsWith(".txt"));
        if (listOfFiles != null) {
            for (File file : listOfFiles) {
                if (file.isFile()) {
                    List<Task> tasks = parseTaskFile(file.getAbsolutePath());
                    Map<Long, List<Task>> groupedTasks = tasks.stream()
                            .filter(task -> task.getStartTime() != null || 
                                            task.isBodSecurity() || 
                                            task.isSodSecurity() || 
                                            task.isUocSecurity())
                            .collect(Collectors.groupingBy(
                                task -> task.getStartTime() != null ? task.getStartTime() : -1L, 
                                TreeMap::new, Collectors.toList()));
                    for (Task task : tasks) {
                        taskEventHandler.handle(task);
                    }
                }
                
            }
        } else {
            LOG.error("No files found in the directory: " + directoryPath);
        }
        taskEventHandler.writeViolationsToFile("../Modeler/example/src/files/violations.txt");
    }    
    
    private List<Task> parseTaskFile(String filePath) {
        List<Task> tasks = new ArrayList<>();
        Map<String, String> subTaskUserTaskMap = new HashMap<>();

        try (BufferedReader br = new BufferedReader(new FileReader(filePath))) {
            String line;
            while ((line = br.readLine()) != null) {
                if (line.startsWith("Element:") || line.startsWith("Instance") || line.startsWith("Priority")) {
                    Task task = parseTaskLine(line);
                    if (task != null) {
                        if (task.getUserTask() != null) {
                            subTaskUserTaskMap.put(task.getIdBpmn(), task.getUserTask());
                        }
                        tasks.add(task);
                    }
                }
            }
        } catch (IOException e) {
            LOG.error("Error reading the task file", e);
        }

        for (Task task : tasks) {
            if (task.isBodSecurity()) {
                List<String> userTasksForSubtasks = task.getSubTasks().stream()
                        .map(subTaskUserTaskMap::get)
                        .filter(Objects::nonNull)
                        .collect(Collectors.toList());
                task.setSubTasksUserTasks(userTasksForSubtasks);
            }
        }
        
        return tasks;
    }

    private Task parseTaskLine(String line) {
        String type = null, name = null, idBpmn = null, userTask = null;
        List<String> subTasks = new ArrayList<>();
        List<String> subTasksUserTasks = new ArrayList<>();
        boolean sodSecurity = false, bodSecurity = false, uocSecurity = false;
        Integer mth = null, instance = null, numberOfExecutions = 1, execution = 0;
        Long startTime = null; 
        Long stopTime = null;
        Long time = null;
    
        if (line.startsWith("Instance")) {
            int colonIndex = line.indexOf(":");
            if (colonIndex != -1) {
                String instancePart = line.substring(0, colonIndex).trim();
                String[] instanceParts = instancePart.split(" ");
                if (instanceParts.length == 2) {
                    try {
                        instance = Integer.parseInt(instanceParts[1]);
                    } catch (NumberFormatException e) {
                        LOG.error("Error parsing instance number", e);
                    }
                }
                line = line.substring(colonIndex + 1).trim();
            } else {
                LOG.error("Instance format incorrect in line: {}", line);
                return null;
            }
        }
    
        int openBracketIndex = line.indexOf("[");
        int closeBracketIndex = line.lastIndexOf("]");
        if (openBracketIndex == -1 || closeBracketIndex == -1) {
            LOG.error("Brackets not found in line: {}", line);
            return null;
        }
    
        String content = line.substring(openBracketIndex + 1, closeBracketIndex);
        String[] parts = content.split(", (?=[a-zA-Z_]+=)");
    
        for (String part : parts) {
            String[] keyValue = part.split("=", 2);
            if (keyValue.length != 2) {
                continue;
            }
            switch (keyValue[0].trim()) {
                case "type":
                    type = keyValue[1].trim();
                    break;
                case "name":
                    name = keyValue[1].trim();
                    break;
                case "id_bpmn":
                    idBpmn = keyValue[1].trim();
                    break;
                case "sodSecurity":
                    sodSecurity = Boolean.parseBoolean(keyValue[1].trim().toLowerCase());
                    break;
                case "bodSecurity":
                    bodSecurity = Boolean.parseBoolean(keyValue[1].trim().toLowerCase());
                    break;
                case "uocSecurity":
                    uocSecurity = Boolean.parseBoolean(keyValue[1].trim().toLowerCase());
                    break;
                case "mth":
                    mth = Integer.parseInt(keyValue[1].trim());
                    break;
                case "userTask":
                    userTask = keyValue[1].trim();
                    break;
                case "subTask":
                    subTasks = Arrays.asList(keyValue[1].replace("\"", "").trim().split("\\s*,\\s*"));
                    break;
                case "startTime":
                    startTime = Long.parseLong(keyValue[1].trim());
                    break;
                case "stopTime":
                    stopTime = Long.parseLong(keyValue[1].trim());
                    break;
                case "time":
                    time = Long.parseLong(keyValue[1].trim());
                    break;
                case "numberOfExecutions":
                    numberOfExecutions = Integer.parseInt(keyValue[1].trim());
                    break;
                case "execution":
                    execution = Integer.parseInt(keyValue[1].trim());
                    break;
            }
        }
    
        LOG.debug("Parsed Task: idBpmn={}, bodSecurity={}, sodSecurity={}, uocSecurity={}, subTasks={}, userTask={}, stopTime={}, numberOfExecutions={}, execution={}",
        idBpmn, bodSecurity, sodSecurity, uocSecurity, subTasks, userTask, stopTime, numberOfExecutions, execution);

    return new Task(type, name, idBpmn, mth, subTasks, userTask, bodSecurity, sodSecurity, uocSecurity, startTime, stopTime, time, instance, numberOfExecutions, execution, subTasksUserTasks);
    } 
}   
