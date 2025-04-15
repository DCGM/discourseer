
homes=$(pwd)

for folder in `ls`; do
	cd $folder && ./run_experiment* recalc
	cd $homes
done

# remove all backups if needed...
# rm -r */*_backup_*
