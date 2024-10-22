#!/bin/bash
# Description: Run experiments in multiple folders with run_experiment.sh script. 
# Usage: ./run_experiment_folders.sh [mini] folder1 folder2 folder3 ...

# get location of this script
HOME_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# check if there are any arguments
if [ "$#" -eq 0 ]; then
	echo "No arguments provided, add folders to run experiments in."
	echo "Usage: ./run_experiment_folders.sh [mini] folder1 folder2 folder3 ..."
	exit 1
fi

MINI=''
# check if mini experiment
if [ "$1" == "mini" ]; then
	echo "Running mini experiments"
	shift
	MINI='mini'
fi

for folder in $@; do
	cd $HOME_DIR

	# check if folder exists
	if [ ! -d $folder ]; then
		echo "Folder $folder not found"
		continue
	fi

	cd $folder
	echo "Working in $(pwd)"

	# check if run_experiment.sh exists
	if [ ! -f run_experiment.sh ]; then
		echo "run_experiment.sh not found in $folder"
		continue
	fi

	echo ""
	echo ""
	echo "----------------------------------------------------------------------"
	echo "          Running experiment in $folder"
	echo "----------------------------------------------------------------------"
	echo ""
	echo ""

	./run_experiment.sh $MINI  # run experiment in the folder
	echo "Experiment in $folder done"
done

echo "All experiments done"
