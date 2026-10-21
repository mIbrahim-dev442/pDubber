import os
import subprocess

input_folder = None
output_folder = None

def main():
    input_folder = input("Input folder containing WAV files: ").strip()
    output_folder = input("Output folder for enhanced files: ").strip()
    input_folder = os.path.abspath(input_folder)
    output_folder = os.path.abspath(output_folder)
    
    if not os.path.isdir(input_folder):
        print("Error: The input folder does not exist.")
    else:
        os.makedirs(output_folder, exist_ok=True)
    
        command = [
            "resemble-enhance",
            input_folder,
            output_folder
        ]
    
        try:
            subprocess.run(command, check=True)
            print(f"Finished! Enhanced audio was saved to:\n{output_folder}")

        except FileNotFoundError:
            print(
                "Resemble Enhance was not found.\n"
                "Install it with:\n"
                "python -m pip install --upgrade resemble-enhance"
            )
    
        except subprocess.CalledProcessError as error:
            print(f"Enhancement failed with exit code {error.returncode}.")
            
if __name__ == "__main__":
    main()
