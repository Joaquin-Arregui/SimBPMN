#!/bin/bash

taskkill //IM mongod.exe //F

mongod --dbpath "../data/db" --logpath "../data/log/mongod.log" --logappend & sleep 5

bash -c "../Backend/scripts/api.sh"
