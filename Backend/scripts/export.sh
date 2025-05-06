#!/bin/bash
echo "Introduzca el nombre del fichero y la extesión deseada (.json o .txt):" 
read NOM
mongoexport --db CEP4BPMSec-api --collection securities --out $NOM


