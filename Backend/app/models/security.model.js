var mongoose = require('mongoose');

var SecuritySchema = mongoose.Schema({
    id_model: { type: String, required: true },
    id_bpmn: { type: String, required: true, unique: true },
    Bod: { type: Boolean, default: false },
    Sod: { type: Boolean, default: false },
    Uoc: { type: Boolean, default: false },
    SubTasks: [
        {
            taskId: String,
            UserTask: String
        }
    ],
    Mth: Number,
    P: Number,
    User: String,
    Log: String,
    NumberOfExecutions: { type: Number, default: 0 },  
    AverageTimeEstimate: { type: Number, default: 0 }, 
    Instance: { type: String, default: '' }  
});

module.exports = mongoose.model('Security', SecuritySchema);
