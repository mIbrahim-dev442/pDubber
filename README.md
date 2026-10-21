<p align="center"><pre align="center">
                _/_/_/              _/        _/
     _/_/_/    _/    _/  _/    _/  _/_/_/    _/_/_/      _/_/    _/  _/_/
    _/    _/  _/    _/  _/    _/  _/    _/  _/    _/  _/_/_/_/  _/_/
   _/    _/  _/    _/  _/    _/  _/    _/  _/    _/  _/        _/
  _/_/_/    _/_/_/      _/_/_/  _/_/_/    _/_/_/      _/_/_/  _/
 _/
_/</pre></p>

<p align="center"><b>An AI dubbing pipeline for movies, shows, or just about anything.</b><br>
Separate the vocals, re-voice every line in the <i>original speaker's own voice</i>, clean it up, and mix it back in.</p>

<p align="center"><a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0-blue.svg" alt="License: GPL-3.0"></a></p>

> PDubber is a useful, personal processing pipeline. It works well when the inputs are good, and the [caveats](#caveats--known-limitations) below are worth reading before you start a 2-hour film.

## Table of Contents

- [What it does](#what-it-does)
- [What it is **not**](#what-it-is-not)
- [Installation](#installation)
- [Requirements](#requirements)
- [Usage](#usage)
- [How it works](#how-it-works)
  - [Details of the generation step](#details-of-the-generation-step)
- [Caveats & known limitations](#caveats--known-limitations)
- [Mixing and ducking](#mixing-and-ducking)
  - [Recommended workflow](#recommended-workflow)
- [Language support](#language-support)
- [Responsible use](#responsible-use)
- [Credits](#credits)
- [License](#license)

## What it does

PDubber takes an **audio track** and an **SRT subtitle file** and produces a **brand-new dubbed audio track** that is timed to the original, with the voices cloned from the people actually speaking.

- **Voice-cloned dubbing, line by line.** For every subtitle cue, PDubber cuts the matching slice out of the original audio and uses it as the voice reference for [Chatterbox TTS](https://github.com/resemble-ai/chatterbox). Each line is spoken in the voice of whoever said it on screen. There is no speaker diarization and no manual voice assignment.

- Every generated clip is placed in a new file at its cue's exact start timestamp, so the dub stays in sync.
- Clips are trimmed of leading and trailing silence, and if the generated speech is longer than its subtitle window it is sped up with `sox tempo` (pitch-preserving) to fit. Clips that already fit are left alone, so the delivery never gets slowed or padded.

- Demucs splits vocals from music and effects, so the background survives untouched and you can lay the dub on top of it.

- **Optional enhancement.** Resemble Enhance denoises and sharpens the TTS output so it sits better against real production audio.

## What it is **not**

Being upfront, because the output is only as good as what you feed it:

- It is **not** a one-click "dub my movie" button. It is four steps you run in order.
- It does **not** translate. It speaks the subtitle text as written (see [Language support](#language-support)).
- It does **not** generate laughs, gasps, grunts, crying, or other non-speech sound unless the subtitle text makes the model produce them.
- It does **not** duck or remove the original vocals for you (see [Mixing and ducking](#mixing-and-ducking)).

## Installation
Conda or some venv is advised. These are the bare minimum. Edit `requirements.txt` if you use RoCM like me.
```bash
git clone https://github.com/mIbrahim-dev442/pDubber.git
cd PDubber
pip install -r requirements.txt
```

Make sure `ffmpeg`, `sox`, and `resemble-enhance` all run from your terminal. On first use, Demucs, Chatterbox, and Resemble Enhance may download their model weights.


## Requirements

- **Python 3.11** (Chatterbox is developed and tested on 3.11; 3.10+ is the minimum)
- **[FFmpeg](https://ffmpeg.org/)** on your `PATH`
- **[SoX](https://sox.sourceforge.net/)** on your `PATH`
- A **CUDA GPU** is strongly recommended
- RoCM works; I use it. Just make sure you have that specific Pytorch + more installed.

Python dependencies can be found in `requirements.txt`

## Usage

```bash
python main.py
```

```
Choose an option:
1) Separate Vocals from Background Audio (Demucs)
2) Generate a Dubbed Audio Track
3) Enhance a [Dubbed] Audio Track
4) Merge an Audio Track with Background Audio
```

Each option prompts for its paths interactively. Quotes around dragged-and-dropped paths are stripped automatically.
## How it works

| Step | Script | Tooling | What happens |
|:--|:--|:--|:--|
| 1. Separate | `separator.py` | [Demucs](https://github.com/facebookresearch/demucs) (`htdemucs`, two-stem) | Splits audio into `vocals` and `no_vocals` (music and effects). |
| 2. Generate | `generator.py` | [Chatterbox TTS](https://github.com/resemble-ai/chatterbox), `ffmpeg`, `sox`, `pysrt`, `pydub` | Per cue: extract reference, clone and speak, trim silence, tempo-fit, save. Then assemble all clips onto a silent timeline matching the source length. |
| 3. Enhance | `enhancer.py` | [Resemble Enhance](https://github.com/resemble-ai/resemble-enhance) | Denoises and enhances a folder of WAV files. |
| 4. Merge | `combiner.py` | `pydub` | Overlays two audio files (for example dub + background) into `output.wav`. |

### Details of the generation step

- **Voice prompt:** the exact cue window (start to end) is cut from the audio you supply and used as the reference clip.
- **Sampling settings:** `exaggeration=0.3` and `cfg_weight=0.1`. The low CFG is deliberate, as it reduces accent bleed from the reference when the language differs from the reference speaker's. See Chatterbox's [tips](https://github.com/resemble-ai/chatterbox#original-chatterbox-tips).
- **Silence trimming:** `ffmpeg silenceremove` removes the dead air Chatterbox sometimes generates, so the tempo math reflects actual speech.
- **Tempo fit:** `multiplier = generated_length / cue_length`, applied only when `> 1`.
- **Output:** per-cue `scaled-N.mp3` clips plus one assembled `final_combined_output.wav` in your chosen folder.

## Caveats & known limitations

These matter more than any feature list.

**Subtitle quality is everything.** The dub is a direct readout of your SRT. Bad timing, merged lines, ads, or sloppy ASR-generated subs give you bad dubs. Use human-made or carefully proofed subtitles, with accurate cue boundaries, one speaker per cue where possible, and no stray `[music]` or credit lines.

**Non-speech needs the original audio.** Laughter, screams, sighs, crowd noise, and ad-libs are not in the subtitles, and TTS does them poorly. Rather than fighting that, **duck the original vocals under the dub** and let the real performance show through in the gaps. See below.


**Reference quality matters.** The cloned voice is only as clean as the slice it was cloned from. Very short cues, overlapping speakers, shouting, music bleed, or whispering give shakier clones. Running Demucs first and pointing the generator at the **vocals stem** gives much cleaner references than the full mix (see the workflow).

**Occasional TTS mishaps.** Chatterbox can hallucinate, drop words, or glitch on very short lines. Spot-check, delete a bad `scaled-N.mp3`, and rerun. The resume logic will regenerate just that one.

## Mixing and ducking

`combiner.py` is a straight overlay (both tracks at full level, aligned at 0:00). It does **not** duck. For a natural result you usually want three layers:

1. **Background** (`no_vocals.wav` from step 1)
2. **Dub** (from step 2 or 3), full level
3. **Original vocals** (`vocals.wav` from step 1), ducked while the dub is speaking, so laughs, breaths, and untranslated moments still come through

One way to do that with `ffmpeg` is a sidechain compressor that lowers the original vocals whenever the dub is active.

Then run your new audio and `no_vocals.wav` through **option 4** to produce the final track.

### Recommended workflow

**0. Pull the audio and subtitles from your video** (skip if you already have them)

```bash
ffmpeg -i movie.mkv -vn -ac 2 -ar 44100 audio.wav
ffmpeg -i movie.mkv -map 0:s:0 subs.srt
```

**1. Separate** (option 1). Gives you `vocals.wav` and `no_vocals.wav` under `<out>/htdemucs/<name>/`.

**2. Generate** (option 2).
- *Audio file:* the **vocals stem** (cleanest voice references) or the original audio.
- *SRT file:* your subtitles.
- *Destination:* a folder to hold the per-line clips and `final_combined_output.wav`.

**3. Enhance** (option 3, optional). Point it at a folder containing the WAV(s) to clean. Put `final_combined_output.wav` in its own folder first, so you do not also process the per-line clips.

**4. Merge** (option 4). Combine the dub with `no_vocals.wav` (and your ducked vocals mix, see above). Output is `output.wav`.

**5. Put it back in the video**

```bash
ffmpeg -i movie.mkv -i output.wav -map 0:v -map 1:a -map 0:s? \
  -c:v copy -c:a aac -b:a 192k -c:s copy dubbed.mkv
```

## Language support

The generator uses the standard English `ChatterboxTTS` model, so the **subtitle text should be English**. The source audio can be anything, and the voices are cloned from it, but what gets spoken is the English in your SRT. That makes PDubber well suited to dubbing foreign films into English from good English subtitles.

For other languages, Chatterbox ships a multilingual model (23+ languages, with `language_id`) that could be swapped into `generator.py`.

## Responsible use

PDubber clones voices. Only use it on audio you have the rights or permission to work with, and do not use it to impersonate people or deceive anyone. Audio generated by Chatterbox carries Resemble AI's imperceptible [PerTh watermark](https://github.com/resemble-ai/perth).

## Credits

PDubber is glue around excellent open-source work:

- [Demucs](https://github.com/facebookresearch/demucs) by Meta AI Research
- [Chatterbox TTS](https://github.com/resemble-ai/chatterbox) by Resemble AI
- [Resemble Enhance](https://github.com/resemble-ai/resemble-enhance) by Resemble AI
- [pydub](https://github.com/jiaaro/pydub), [pysrt](https://github.com/byroot/pysrt), [FFmpeg](https://ffmpeg.org/), and [SoX](https://sox.sourceforge.net/)

## License

PDubber is free software, released under the [GNU General Public License v3.0](LICENSE).

Copyright (C) 2026 &lt;Muhammad Ibrahim&gt;

You are free to use, study, modify, and share it. If you distribute it or a modified version, you must do so under the same license, keep this copyright notice, and make your source code available. It comes with no warranty.

The tools and models PDubber builds on (Demucs, Chatterbox, Resemble Enhance, and the rest) keep their own licenses.
