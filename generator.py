import pysrt
import subprocess
import os
from datetime import datetime
import torchaudio as ta
from chatterbox import ChatterboxTTS
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
import torch


def file_verifier(file_path):
    if not os.path.isfile(file_path):
        exit()


def folder_verifier(folder_path):
    if not os.path.exists(folder_path):
        print("Creating folder.")
        os.makedirs(folder_path, exist_ok=True)


def generate_audio_clips(audio_path, save_folder, modelnorm, subs):
    for sub_index, sub in enumerate(subs):
        final_filename = os.path.join(save_folder, f"scaled-{sub_index}.mp3")
        # Resuming after a generation failure
        if os.path.exists(final_filename):
            print(f"Skipping index {sub_index} - File already exists in Drive.")
            continue
        print(f"Processing index {sub_index}: {sub.text}")
        start = str(sub.start)
        end = str(sub.end)
        fmt = "%H:%M:%S,%f"
        t1 = datetime.strptime(start, fmt)
        t2 = datetime.strptime(end, fmt)
        elapsed = t2 - t1
        startts = t1.strftime("%H:%M:%S.%f")[:-3]
        duration = f"{elapsed.total_seconds():.3f}"
        # Temp files for prompt reference
        extract_filename = f"{sub_index}.mp3"
        cmd = [
            "ffmpeg", "-y",
            "-ss", startts,
            "-i", audio_path,
            "-t", duration,
            "-acodec", "libmp3lame",
            extract_filename
        ]
        subprocess.run(cmd, capture_output=True, text=True)
        tts_filename = f"tts-{sub_index}.wav"
        try:
            # 1. Main attempt: Low CFG to neutralize random accents
            wav = modelnorm.generate(
                str(sub.text),
                audio_prompt_path=extract_filename,
                exaggeration=0.3,
                cfg_weight=0.1
            )
            ta.save(tts_filename, wav, modelnorm.sr)
        except Exception as e:
            print(f"Error generating with prompt on index {sub_index}: {e}")
            print("Falling back to absolute model defaults...")
            # 2. Bulletproof Fallback: Pure text generation with zero custom parameters
            try:
                wav = modelnorm.generate(str(sub.text))
                ta.save(tts_filename, wav, modelnorm.sr)
            except Exception as fallback_error:
                print(f"Critical failure on index {sub_index}: {fallback_error}")
                continue  # Skip this segment so your script doesn't completely stop
        # --- Trim leading and trailing silence from the generated TTS audio ---
        # --- Accounts for excessive silent tokens. ---
        trimmed_tts_filename = f"trimmed-{sub_index}.wav"
        trim_cmd = [
            "ffmpeg", "-y",
            "-i", tts_filename,
            "-af", (
                "silenceremove="
                "start_periods=1:start_duration=0.01:start_threshold=-75dB:" # Barely sensitive start
                "stop_periods=1:stop_duration=0.2:stop_threshold=-55dB"      # Normal end trimming
            ),
            trimmed_tts_filename
        ]
        subprocess.run(trim_cmd, capture_output=True, text=True)
        original_audio_length = float(len(AudioSegment.from_file(extract_filename)))
        generated_audio_length = float(len(AudioSegment.from_file(trimmed_tts_filename)))   # use trimmed file
        scale_tts = generated_audio_length/original_audio_length
        try:
            if scale_tts > 1:
                multiplier = scale_tts
            else:
                multiplier = 1.0
        except:
            multiplier = 1.0
        scaled_wav_filename = f"scaled-{sub_index}.wav"
        pitch_cmds = [
            "sox",
            trimmed_tts_filename,          # scale the trimmed audio
            scaled_wav_filename,
            "tempo",
            f"{round(multiplier, 3)}"
        ]
        subprocess.run(pitch_cmds)
        # Save the final output directly to the Drive path
        subprocess.run([
            "ffmpeg", "-y",
            "-i", scaled_wav_filename,
            final_filename
        ])
        # Cleanup local temp files (including the new trimmed file)
        if os.path.exists(tts_filename): os.remove(tts_filename)
        if os.path.exists(extract_filename): os.remove(extract_filename)
        if os.path.exists(scaled_wav_filename): os.remove(scaled_wav_filename)
        if os.path.exists(trimmed_tts_filename): os.remove(trimmed_tts_filename)
    print(f"All files saved to {save_folder}")


def analyze_original_track(audio_path):
    print("Analyzing original track duration...")
    try:
        # Load original track briefly just to capture its exact millisecond duration
        original_audio = AudioSegment.from_file(audio_path)
        total_duration_ms = len(original_audio)
        print(f" -> Total timeline duration: {total_duration_ms / 1000:.2f} seconds.")
        del original_audio  # Clear it from RAM immediately to keep footprint low
        return total_duration_ms
    except Exception as e:
        print(f" [CRITICAL ERROR] Failed to analyze {audio_path}: {e}")
        exit(1)


def combine_audio_clips(audio_path, save_folder, subs):
    # --- TRACK CONFIGURATION ---
    OUTPUT_NAME = "final_combined_output.wav"
    # ---------------------
    total_duration_ms = analyze_original_track(audio_path)
    print("Generating clean, silent digital audio canvas...")
    # Create a 100% silent canvas matching the exact timeline length
    final_mix = AudioSegment.silent(duration=total_duration_ms, frame_rate=44100)
    print("Processing and placing TTS segments onto the new timeline...")
    overlay_count = 0
    skipped_count = 0
    for i, sub in enumerate(subs):
        clip_path = os.path.join(save_folder, f"scaled-{i}.mp3")
        # Verify the file exists before attempting to overlay
        if not os.path.exists(clip_path):
            continue
        # Clean, native millisecond extraction from pysrt (bypasses string parsing)
        delay_ms = sub.start.ordinal
        # --- SAFE AUDIO LOADING & OVERLAY BLOCK ---
        try:
            # Load the specific voice clip
            voice_clip = AudioSegment.from_file(clip_path)
            # Paste the voice clip directly onto the silent timeline
            final_mix = final_mix.overlay(voice_clip, position=delay_ms)
            overlay_count += 1
        except CouldntDecodeError:
            print(f" -> [WARNING] Skipping index {i}: File is corrupted or has a fake layout ({clip_path})")
            skipped_count += 1
        except Exception as e:
            print(f" -> [WARNING] Skipping index {i} due to unexpected error: {e}")
            skipped_count += 1
        # ------------------------------------------
        if (i + 1) % 50 == 0:
            print(f" -> Processed {i + 1}/{len(subs)} segments...")
    print(f"\nCompilation completed summary:")
    print(f" -> Successfully mixed: {overlay_count} tracks.")
    print(f" -> Safely skipped: {skipped_count} bad files.")
    # Export final high-quality master file as WAV
    final_output_path = os.path.join(save_folder, OUTPUT_NAME)
    print(f"Exporting final clean track to {final_output_path}...")
    final_mix.export(
        final_output_path,
        format="wav"
    )
    print("Success! Your brand new, standalone audio track is saved.")


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    audio_path = input("Where is your audio file? (File path): ").strip('"')
    srt_path = input("Where is your subtitle (SRT) file? (File path): ").strip('"')
    save_folder = input("Where would you like to save your audio clips? (Destination Path): ").strip('"')
    file_verifier(audio_path)
    file_verifier(srt_path)
    folder_verifier(save_folder)
    modelnorm = ChatterboxTTS.from_pretrained(device=device)
    subs = pysrt.open(srt_path)
    generate_audio_clips(audio_path, save_folder, modelnorm, subs)
    combine_audio_clips(audio_path, save_folder, subs)


if __name__ == "__main__":
    main()
