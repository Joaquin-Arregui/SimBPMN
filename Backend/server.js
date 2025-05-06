var express = require('express');
var bodyParser = require('body-parser');
var cors = require('cors');

var app = express();
var allowedOrigins = [
    'http://localhost:8080',
    'http://localhost:9000'
];
app.use(cors({
    origin: function (origin, callback) {
        if (!origin) return callback(null, true);
        if (allowedOrigins.indexOf(origin) === -1) {
            var msg = 'El CORS policy para este sitio no permite acceso desde el origen especificado.';
            return callback(new Error(msg), false);
        }
        return callback(null, true);
    },
    methods: "GET,HEAD,PUT,PATCH,POST,DELETE",
    credentials: true
}));

app.use(bodyParser.urlencoded({ extended: true }));

app.use(bodyParser.json());

var dbConfig = require('./config/database.config.js');
var mongoose = require('mongoose');

mongoose.Promise = global.Promise;

mongoose.connect(dbConfig.url).then(() => {
}).catch(err => {
    console.error('Could not connect to the database. Exiting now...', err);
    process.exit();
});

app.get('/', function (req, res) {
    res.json({"message": "Welcome to BPMN security tasks modeller"});
});

require('./app/routes/security.routes.js')(app);

app.listen(3000, function () {
    console.log("Server is listening on port 3000");
});
