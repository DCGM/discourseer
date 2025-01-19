# test default experiment automatically

echo -e "\n\n_____prepare_ratings.sh_____\n\n" && \
./prepare_ratings.sh && \
echo -e "\n\n_____run_experiment.sh_____\n\n" && \
./run_experiment.sh && \
echo -e "\n\n_____recalc_irr_for_dataframe.sh_____\n\n" && \
./recalc_irr_for_dataframe.sh
exit $?  # exit with the exit code of the last command