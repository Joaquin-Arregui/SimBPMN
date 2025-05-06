const Security = require('../models/security.model.js');
const fs = require('fs');
const path = require('path');

exports.create = function (req, res) {

    if (req.body.Bod === undefined || req.body.Sod === undefined || req.body.Uoc === undefined) {
        return res.status(400).send({ message: "Security task can not be empty" });
    }

    const security = new Security({
        id_model: req.body.id_model,
        id_bpmn: req.body.id_bpmn || "Untitled security task",
        Bod: req.body.Bod === true,
        Sod: req.body.Sod === true,
        Uoc: req.body.Uoc === true,
        Mth: Number(req.body.Mth),
        P: Number(req.body.P),
        User: req.body.User || '',
        Log: req.body.Log || '',
        NumberOfExecutions: req.body.NumberOfExecutions || 0,
        AverageTimeEstimate: req.body.AverageTimeEstimate || 0,
        Instance: req.body.Instance || ''
    });

    security.save(function (err, data) {
        if (err) {
            console.error(err);
            res.status(500).send({ message: "Some error occurred while creating the Security task." });
        } else {
            res.send(data);
        }
    });
};

exports.esperRules = function (req, res) {
    let ms = "";

    if (!req.body.esperRules) {
        return res.status(400).send({ message: "No esperRules data provided" });
    }

    for (let i = 0; i < req.body.esperRules.length; i++) {
        const st = req.body.esperRules[i];

        const subTasks = st.SubTasks || [];

        const validUserTasks = subTasks.map(subTask => subTask.UserTask)
                                        .filter(userTask => userTask && userTask.trim() !== "" && userTask !== "Unknown");


        const areUserTasksDifferent = new Set(validUserTasks).size > 1;

        const isBoD = st.Bod === true && !areUserTasksDifferent;
        const isSoD = st.Sod === true && areUserTasksDifferent && validUserTasks.length === subTasks.length;
        const isUoC = st.Uoc === true && st.Mth >= 4 && validUserTasks.length > 0;
        if (isBoD) {
            if (subTasks.length >= 2) {
                const subTask1Id = subTasks[0].taskId;
                const subTask2Id = subTasks[1].taskId;
                const user = subTasks[1].UserTask;

                ms += "---------------------------------\n";
                ms += "- [BOD MONITOR] Binding of Duty detected:\n";
                ms += "- Parent Task ID: " + st.id_bpmn + "\n";
                ms += "- SubTask 1 ID: " + subTask1Id + "\n";
                ms += "- SubTask 2 ID: " + subTask2Id + "\n";
                ms += "- User ID: " + user + "\n";
                ms += "---------------------------------\n\n";
            }
        }

        if (isSoD) {
            if (subTasks.length >= 2) {
                const subTask1Id = subTasks[0].taskId;
                const subTask2Id = subTasks[1].taskId;
                const user1 = subTasks[0].UserTask;
                const user2 = subTasks[1].UserTask;

                ms += "---------------------------------\n";
                ms += "- [SOD MONITOR] Separation of Duties detected:\n";
                ms += "- Parent Task ID: " + st.id_bpmn + "\n";
                ms += "- SubTask 1 ID: " + subTask1Id + " - User ID: " + user1 + "\n";
                ms += "- SubTask 2 ID: " + subTask2Id + " - User ID: " + user2 + "\n";
                ms += "---------------------------------\n\n";
            }
        }

        if (isUoC) {
            const userTaskCount = validUserTasks.reduce((acc, userTask) => {
                acc[userTask] = (acc[userTask] || 0) + 1;
                return acc;
            }, {});

            let ruleTriggered = false;
            for (const [user, count] of Object.entries(userTaskCount)) {
                if (count >= st.Mth) {
                    const taskIds = subTasks.map(subTask => subTask.taskId).join(", ");
                    ms += "---------------------------------\n";
                    ms += "- [UOC MONITOR] Usage of Control detected:\n";
                    ms += "- Parent Task ID: " + st.id_bpmn + "\n";
                    ms += "- SubTasks IDs: " + taskIds + "\n";
                    ms += "- User ID: " + user + "\n";
                    ms += "- Maximum allowed executions (Mth >= 4): " + st.Mth + "\n";
                    ms += "---------------------------------\n\n";
                    ruleTriggered = true;
                }
            }
        }
    }

    const filePath = path.join(__dirname, '..', 'esperRules', 'esperRules.txt');
    fs.mkdir(path.dirname(filePath), { recursive: true }, (err) => {
        if (err) {
            console.error('Error creating directory:', err);
            return res.status(500).send({ message: "Error creating directory for esperRules file." });
        }

        fs.writeFile(filePath, ms, function (err) {
            if (err) {
                console.error('Error writing file:', err);
                return res.status(500).send({ message: "Error writing esperRules rules to file." });
            } else {
                res.send({ status: 'esperRules rules generated and file written successfully' });
            }
        });
    });
};

const { exec, spawn } = require('child_process');

const FILES_DIRECTORY = path.resolve(__dirname, '../../../Simulator/files/');
const SIMULATOR_DIRECTORY = path.resolve(__dirname, '../../../Simulator');
const DIAGNOSIS_DIRECTORY = path.resolve(__dirname, '../../../Diagnosis');
const ENGINE_DIRECTORY = path.resolve(__dirname, '../../../Engine');

exports.saveEsperFile = (req, res) => {
    const { content, filename } = req.body;

    if (!content || !filename) {
        return res.status(400).send({ message: 'El contenido o el nombre del archivo faltan' });
    }
    const filePath = path.join(FILES_DIRECTORY, filename);
    fs.writeFile(filePath, content, 'utf8', (err) => {
        if (err) {
            console.error('Error al guardar el archivo:', err);
            return res.status(500).send({ message: 'Error al guardar el archivo' });
        }
        exec(`python main.py`, { cwd: SIMULATOR_DIRECTORY }, (error, stdout, stderr) => {
            if (error) {
                console.error(`Error al ejecutar el simulador: ${error.message}`);
                return res.status(500).send({ message: 'Error al ejecutar el simulador' });
            }
            if (stderr) {
                console.error(`Error en el simulador: ${stderr}`);
            }
            exec('mvn clean install && mvn exec:java', { cwd: ENGINE_DIRECTORY, maxBuffer: 1024 * 1024 * 10 }, (mvnError, mvnStdout, mvnStderr) => {
                if (mvnError) {
                    console.error(`Error executing mvn exec:java: ${mvnError.message}`);
                    return res.status(500).send({ message: 'Error al ejecutar mvn exec:java' });
                }
                fs.readdir(FILES_DIRECTORY, (err, files) => {
                    if (err) {
                        console.error(`Error al leer la carpeta: ${err.message}`);
                        return res.status(500).send({ message: 'Error al leer la carpeta de archivos' });
                    }
                    files.forEach(file => {
                        const filePath = path.join(FILES_DIRECTORY, file);
                        fs.unlink(filePath, (unlinkErr) => {
                            if (unlinkErr) {
                                console.error(`Error deleting file: ${filePath}`, unlinkErr);
                            } else {
                            }
                        });
                    });
                    const violationsFilePath = path.join(__dirname, '..', '..', '..', 'Modeler', 'example', 'src', 'files', 'violations.txt');
                    fs.readFile(violationsFilePath, 'utf8', (err, data) => {
                        if (err) {
                            console.error('Error al leer violations.txt:', err);
                            return res.status(500).send({ message: 'Error al leer violations.txt' });
                        }
                        fs.unlink(violationsFilePath, (unlinkErr) => {
                            if (unlinkErr) {
                                console.error('Error al eliminar violations.txt:', unlinkErr);
                            } else {
                                res.send({ content: data });
                                console.log('Compliance completed succesfully');
                            }
                        });
                    });
                });
            });
        });
    });
};

exports.startChatBot = (req, res) => {
    console.log("Chatbot process started.")
    const { content, diagramXML, filename, diagramfilename } = req.body;
    if (!content || !filename) {
        return res.status(400).send({ message: 'El contenido o el nombre del archivo faltan' });
    }
    const filePath = path.join(FILES_DIRECTORY, filename);
    const diagramPath = path.join(FILES_DIRECTORY, diagramfilename);
    fs.writeFile(filePath, content, 'utf8', (err) => {
        if (err) {
            console.error('Error al guardar el archivo:', err);
            return res.status(500).send({ message: 'Error al guardar el archivo' });
        }
        fs.writeFile(diagramPath, diagramXML, 'utf8', (err) => {
            if (err) {
                console.error('Error al guardar el diagrama:', err);
                return res.status(500).send({ message: 'Error al guardar el diagrama' });
            }
            exec(`python main.py`, { cwd: SIMULATOR_DIRECTORY }, (error, stdout, stderr) => {
                if (error) {
                    console.error(`Error al ejecutar el simulador: ${error.message}`);
                    return res.status(500).send({ message: 'Error al ejecutar el simulador' });
                }
                if (stderr) {
                    console.error(`Simulador stderr: ${stderr}`);
                }
                exec('mvn clean install && mvn exec:java', {cwd: ENGINE_DIRECTORY, maxBuffer: 1024 * 1024 * 10}, (mvnError, mvnStdout, mvnStderr) => {
                    if (mvnError) {
                        console.error(`Error executing mvn exec:java: ${mvnError.message}`);
                        return res.status(500).send({ message: 'Error al ejecutar mvn exec:java' });
                    }
                    if (mvnStderr) {
                        console.error(`Maven stderr: ${mvnStderr}`);
                    }
                    res.send({ content: "Simulation processed succesfully" });
                });
            });
        });
    });
};

exports.getHeatMap = (req, res) => {
    const { content, diagramXML, filename, diagramfilename } = req.body;
    if (!content || !diagramXML || !filename) {
        return res.status(400).send({ message: 'El contenido, el diagrama o el nombre del archivo faltan' });
    }
    const filePath = path.join(FILES_DIRECTORY, filename);
    const diagramPath = path.join(FILES_DIRECTORY, diagramfilename);
    fs.writeFile(filePath, content, 'utf8', (err) => {
        if (err) {
            console.error('Error al guardar el archivo:', err);
            return res.status(500).send({ message: 'Error al guardar el archivo' });
        }
        fs.writeFile(diagramPath, diagramXML, 'utf8', (err) => {
            if (err) {
                console.error('Error al guardar el diagrama:', err);
                return res.status(500).send({ message: 'Error al guardar el diagrama' });
            }
            exec(`python mainGenerateHeatMap.py`, { cwd: SIMULATOR_DIRECTORY }, (error, stdout, stderr) => {
                if (error) {
                    console.error(`Error al ejecutar el simulador: ${error.message}`);
                    return res.status(500).send({ message: 'Error al ejecutar el simulador' });
                }
                if (stderr) {
                    console.error(`Error en el simulador: ${stderr}`);
                }
                fs.readFile(diagramPath, 'utf8', (err, data) => {
                    if (err) {
                        console.error('Error al leer diagram.bpmn:', err);
                        return res.status(500).send({ message: 'Error al leer diagram.bpmn' });
                    }
                    res.send({ content: data });
                    fs.unlink(diagramPath, (unlinkErr) => {
                        if (unlinkErr) {
                            console.error('Error al eliminar violations.txt:', unlinkErr);
                        }
                    });
                });
            });
        });
    });
};

exports.findAll = async function (req, res) {
    try {
        const securities = await Security.find();
        res.send(securities);
    } catch (err) {
        console.error(err);
        res.status(500).send({ message: "Some error occurred while retrieving security tasks." });
    }
};
exports.findModel = function (req, res) {
    Security.find({ id_model: req.params.id_model }, function (err, securities) {
        if (err) {
            console.error(err);
            res.status(500).send({ message: "Some error occurred while retrieving security tasks." });
        } else {
            res.send(securities);
        }
    });
};
exports.findOne = function (req, res) {
    Security.findById(req.params.securityId, function (err, security) {
        if (err) {
            console.error(err);
            if (err.kind === 'ObjectId') {
                return res.status(404).send({ message: "Security task not found with id " + req.params.securityId });
            }
            return res.status(500).send({ message: "Error retrieving security task with id " + req.params.securityId });
        }

        if (!security) {
            return res.status(404).send({ message: "Security task not found with id " + req.params.securityId });
        }

        res.send(security);
    });
};
exports.update = async function (req, res) {
    try {
        const security = await Security.findById(req.params.securityId);
        if (!security) {
            return res.status(404).send({ message: "Security task not found with id " + req.params.securityId });
        }
        if (req.body.id_model !== undefined) security.id_model = req.body.id_model;
        if (req.body.id_bpmn !== undefined) security.id_bpmn = req.body.id_bpmn;
        if (req.body.Bod !== undefined) security.Bod = req.body.Bod;
        if (req.body.Sod !== undefined) security.Sod = req.body.Sod;
        if (req.body.Uoc !== undefined) security.Uoc = req.body.Uoc;
        if (req.body.Mth !== undefined) security.Mth = req.body.Mth;
        if (req.body.P !== undefined) security.P = req.body.P;
        if (req.body.User !== undefined) security.User = req.body.User;
        if (req.body.Log !== undefined) security.Log = req.body.Log;
        if (req.body.SubTasks !== undefined) security.SubTasks = req.body.SubTasks;
        if (req.body.NumberOfExecutions !== undefined) security.NumberOfExecutions = req.body.NumberOfExecutions;
        if (req.body.AverageTimeEstimate !== undefined) security.AverageTimeEstimate = req.body.AverageTimeEstimate;
        if (req.body.Instance !== undefined) security.Instance = req.body.Instance;

        const updatedSecurity = await security.save();
        res.send(updatedSecurity);
    } catch (err) {
        console.error(err);
        res.status(500).send({ message: "Could not update security task with id " + req.params.securityId });
    }
};

exports.delete = function (req, res) {
    Security.findByIdAndRemove(req.params.securityId, function (err, security) {
        if (err) {
            console.error(err);
            if (err.kind === 'ObjectId') {
                return res.status(404).send({ message: "Security task not found with id " + req.params.securityId });
            }
            return res.status(500).send({ message: "Could not delete security task with id " + req.params.securityId });
        }

        if (!security) {
            return res.status(404).send({ message: "Security task not found with id " + req.params.securityId });
        }

        res.send({ message: "Security task deleted successfully!" });
    });
};
