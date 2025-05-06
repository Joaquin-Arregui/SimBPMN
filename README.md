# XSecBPMN

## Prerequisites

Before running the project, ensure that you have the following software installed:

### Global Requirements

1. **Git**
   - For cloning the repository and version control.
   - [Download Git](https://github.com/ajvarela/caise2025/)
   - Verify installation:
     ```bash
     git --version
     ```

2. **Java Development Kit (JDK) 1.8 or higher**
   - Required for the **Engine** module.
   - [Download JDK](https://www.oracle.com/java/technologies/javase-downloads.html)
   - Verify installation:
     ```bash
     java -version
     ```

3. **Apache Maven**
   - Required for building the **Engine** module.
   - [Download Maven](https://maven.apache.org/)
   - Verify installation:
     ```bash
     mvn -version
     ```

4. **Node.js v16 or higher**
   - Required for the **Backend** and **Modeler** modules.
   - [Download Node.js](https://nodejs.org/)
   - Verify installation:
     ```bash
     node -v
     npm -v
     ```

5. **Python 3.7 or higher**
   - Required for the **Simulator** module.
   - [Download Python](https://www.python.org/)
   - Verify installation:
     ```bash
     python --version
     pip --version
     ```

---

### Module-Specific Requirements

#### Simulator

- **Python Packages** are specified in `simulator/requirements.txt`.

- **Install Dependencies**:
```bash
cd Simulator
pip install -r requirements.txt
```

#### Backend

- **Dependencies** are specified in `backend/package.json`.

- **Install Dependencies**:
```bash
cd Backend
npm install
```

#### Modeler

- **Dependencies** are specified in `modeler/package.json`.

- **Install Dependencies**:
```bash
cd Modeler
npm install
```

#### Engine

- **Dependencies** are specified in `engine/pom.xml`.

- **Build the Engine Module**:
```bash
cd Engine
mvn clean install
```

## How to Run the Project

Once all prerequisites are installed, you can run the entire project with a single command:

 - **Navigate to the Root Folder**:
```bash
cd XSecBPMN
```

 - **Run the project**:
On Windows, execute the following command from the root directory:
```bash
./start.bat
```
or
```bash
start.bat
```
This script will handle the execution and orchestration of all modules.