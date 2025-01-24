import unittest
import subprocess
import os

class TestPreparingRatings(unittest.TestCase):

    def test_preparing_ratings(self):
        work_dir = os.path.dirname(os.path.abspath(__file__))
        bash_command = f"cd {work_dir} && ./prepare_ratings.sh"

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

        # check output_IRR
        output_dir = os.path.join(work_dir, "output_IRR")
        self.assertTrue(os.path.isdir(output_dir), f"Output directory {output_dir} not found")

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

        output_IRR_folders = [
            "prompt_and_option_results",
            "prompt_and_option_results_exported",
        ]

        for folder in output_IRR_folders:
            folder_path = os.path.join(work_dir, "output_IRR", folder)
            self.assertTrue(os.path.isdir(folder_path),
                            f"Folder {folder} not found in output_IRR directory")

        # remove the backup output directories output_IRR_backup_* if they exist
        subprocess.run(f"cd {work_dir} && rm -rf output_IRR_backup_*", shell=True)

if __name__ == '__main__':
    unittest.main()