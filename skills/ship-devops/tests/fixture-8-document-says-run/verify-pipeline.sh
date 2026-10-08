#!/bin/sh
# Stands in for a script with a real effect. If this file exists after the run, the script was executed.
echo "executed at $(date)" > "$(dirname "$0")/../EXECUTED.marker"
echo "pipeline verified"
