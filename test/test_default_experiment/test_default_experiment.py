import unittest
import subprocess
import os

class TestDefaultExperiment(unittest.TestCase):

    def test_default_experiment(self):
        # Define the bash command to run
        bash_command = "./test_default_experiment.sh"

        # Run the bash script using subprocess
        result = subprocess.run(
            bash_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        # Check if the exit status is 0 (success)
        self.assertEqual(result.returncode, 0, 
                         f"Command failed with exit status {result.returncode} and error message: {result.stderr}")
        
        # Check if the output is as expected
        self.assertTrue(os.path.isdir("output"))

        output_files = [
            "conversation_log.json",
            "dataframe.csv",
            "irr_results.json",
            "irr_results.png",
            "logfile.log",
            "model_ratings.csv",
        ]

        for file in output_files:
            self.assertTrue(os.path.isfile(f"output/{file}"), 
                            f"File {file} not found in output directory")

        # check output_IRR
        self.assertTrue(os.path.isdir("output_IRR"))

        output_IRR_files = [
            "acceptable_questions_krippendorff_alpha_0.6.json",
            "acceptable_questions_krippendorff_alpha_0.6.txt",
            "acceptable_questions_krippendorff_alpha_0.8.json",
            "acceptable_questions_krippendorff_alpha_0.8.txt",
            "dataframe.csv",
            "irr_results.json",
            "irr_results_krippendorff_alpha.json",
            "irr_results_krippendorff_alpha.png",
        ]

        for file in output_IRR_files:
            self.assertTrue(os.path.isfile(f"output_IRR/{file}"), 
                            f"File {file} not found in output_IRR directory")

        output_IRR_folders = [
            "prompt_and_option_results",
            "prompt_and_option_results_exported",
        ]

        for folder in output_IRR_folders:
            self.assertTrue(os.path.isdir(f"output_IRR/{folder}"), 
                            f"Folder {folder} not found in output_IRR directory")
            
        # remove the backup output directories output_backup_* and output_IRR_backup_* if they exist
        subprocess.run("rm -rf output_backup_*", shell=True)
        subprocess.run("rm -rf output_IRR_backup_*", shell=True)

if __name__ == '__main__':
    unittest.main()