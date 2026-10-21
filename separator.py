import os
import demucs.separate

file_path=None
save_folder=None

def file_verifier(file_path, save_folder):
    if not os.path.isfile(file_path):
        exit()
    if not os.path.exists(save_folder):
        print("Creating folder.")
        os.makedirs(save_folder, exist_ok=True)

def separate(file_path, save_folder):
    demucs.separate.main([
        "--two-stems", "vocals",
        "-n", "htdemucs",
        "-o", save_folder,
        file_path,
    ])

def main():
    file_path=input("Where is your audio file? (File path): ").strip('"')
    save_folder=input("Where would you like to save your stems? (Destination Path): ").strip('"')
    file_verifier(file_path, save_folder)
    separate(file_path, save_folder)

if __name__ == "__main__":
    main()
