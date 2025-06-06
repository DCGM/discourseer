import unittest
import subprocess
import os

class TestDefaultExperiment(unittest.TestCase):

    def test_default_experiment(self):
        # Define the bash command to run
        work_dir = os.path.dirname(os.path.abspath(__file__))
        bash_command = f"cd {work_dir} && ./test_default_experiment.sh"

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
        output_dir = os.path.join(work_dir, "output")
        self.assertTrue(os.path.isdir(output_dir), f"Output directory {output_dir} not found")

        output_files = [
            "conversation_log.json",
            "dataframe.csv",
            "irr_results.json",
            "irr_results.png",
            "logfile.log",
            "model_ratings.csv",
        ]

        for file in output_files:
            file_path = os.path.join(work_dir, "output", file)
            self.assertTrue(os.path.isfile(file_path),
                            f"File {file} not found in output directory")

        # check output_IRR
        output_IRR_dir = os.path.join(work_dir, "output_IRR")
        self.assertTrue(os.path.isdir(output_IRR_dir), f"Output directory {output_IRR_dir} not found")

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
            file_path = os.path.join(work_dir, "output_IRR", file)
            self.assertTrue(os.path.isfile(file_path),
                            f"File {file} not found in output_IRR directory")
            
        # remove the backup output directories output_backup_* and output_IRR_backup_* if they exist
        subprocess.run(f"cd {work_dir} && rm -rf output_backup_*", shell=True)
        subprocess.run(f"cd {work_dir} && rm -rf output_IRR_backup_*", shell=True)

if __name__ == '__main__':
    unittest.main()