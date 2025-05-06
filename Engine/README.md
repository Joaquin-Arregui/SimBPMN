ALBA
==================
Firts steps for the project ALBA


Requirements
============
Java: 170.128
Maven: 3.11.0


Setup
=====

To run demo:

1. Open a terminal window

2. Navigate to the root directory of the project (where the pom.xml is)

3. Modify the "RandomTaskEventGenerator.java" to trigger a specific rule.

4. 'mvn clean install' (this will compile and build the project)

5. Now, you can choose to run RandomTaskEventGenerator with: 'mvn exec:java -Dexec.args="random 1000"' or use TaskProcessor with: 'mvn exec:java -Dexec.mainClass="com.cor.cep.StartDemo" -Dexec.args="file"'

	
