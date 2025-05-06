#!/bin/bash

cd ../Backend

taskkill //IM node.exe //F

node ./server.js
