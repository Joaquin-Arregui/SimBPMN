package com.cor.cep;

import java.io.File;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.context.support.ClassPathXmlApplicationContext;
import com.cor.cep.util.TaskProcessor;

/**
 * Entry point for the Demo. Run this from your IDE, or from the command line using 'mvn exec:java'.
 */
public class StartDemo {

    private static final Logger LOG = LoggerFactory.getLogger(StartDemo.class);

    public static void main(String[] args) throws Exception {

        LOG.debug("Starting application...");

        long noOfTemperatureEvents = 1000;
        String mode = "file";

        if (args.length >= 1) {
            mode = args[0].trim().toLowerCase();
        }        

        if (args.length >= 2) {
            try {
                noOfTemperatureEvents = Long.valueOf(args[1]);
            } catch (NumberFormatException e) {
                LOG.error("Invalid number format for events: {}. Using default value.", args[1], e);
            }
        } else {
            LOG.debug("No override of number of events detected - defaulting to {} events.", noOfTemperatureEvents);
        }

        ClassPathXmlApplicationContext appContext = new ClassPathXmlApplicationContext("application-context.xml");
        BeanFactory factory = appContext;

        TaskProcessor taskProcessor = (TaskProcessor) factory.getBean("taskProcessor");

        String directoryPath = "../Simulator/files/";
        File directory = new File(directoryPath);

        String canonicalPath = directory.getCanonicalPath();

        taskProcessor.processXESFiles(directoryPath);
        //taskProcessor.processTaskFiles(directoryPath);
    }
}
