# SimBPMN

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

2. **Python 3.10.0 or higher**
   - Required for the **Backend** module.
   - [Download Python](https://www.python.org/downloads/release/python-3100//)
   - Verify installation:
     ```bash
     python --version
     ```

3. **Node.js v16 or higher**
   - Required for the **Modeler** module.
   - [Download Node.js](https://nodejs.org/)
   - Verify installation:
     ```bash
     node -v
     npm -v
     ```

### Module-Specific Requirements

#### Backend

- **Dependencies** are specified in `requirements.txt`.

- **Install Dependencies**:
```bash
cd Backend
pip install -r requirements.txt
```

#### Modeler

- **Dependencies** are specified in `modeler/package.json`.

- **Install Dependencies**:
```bash
cd Modeler
npm install
```

## How to Run the Project

Once all prerequisites are installed, you can run the entire project with a single command:

 1. **Navigate to the Root Folder**:
```bash
cd SimBPMN
```

 2. **Run the project**:
On Windows, execute the following command from the root directory:
```bash
./run.bat
```
This script will handle the execution and orchestration of all modules.