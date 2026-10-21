import os
from pydub import AudioSegment


def folder_verifier(save_folder):
    if not os.path.exists(save_folder):
        print("Creating folder.")
        os.makedirs(save_folder, exist_ok=True)
        
def file_verifier(file_path):
    if not os.path.isfile(file_path):
        exit()

def main():
    audio1_path = input("Where is your first audio file? (File path): ").strip('"')
    audio2_path = input("Where is your second audio file? (File path): ").strip('"')
    output_folder=input("Where would you like to save your combined audio? (Destination Path): ").strip('"')
    file_verifier(audio1_path)
    file_verifier(audio2_path)
    folder_verifier(output_folder)
    final_audio = AudioSegment.from_file(audio1_path).overlay(AudioSegment.from_file(audio2_path), position=0)
    output_path = os.path.join(output_folder, "output.wav")
    final_audio.export(output_path, format="wav")
        
if __name__ == "__main__":
    main()
