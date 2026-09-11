# AI Utilities Appliance

## setup
lxc profile create transcription
lxc profile edit transcription
lxc launch ubuntu:24.04 transcription -p default -p transcription
lxc exec transcription -- bash

### install
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv --python 3.12 --seed --managed-python
source .venv/bin/activate

uv pip install whisperx
uv pip install --system huggingface_hub 

mkdir ~/workspace/files
mkdir ~/workspace/models

make push_files

hf download NbAiLab/nb-whisper-large \
  --local-dir ~/workspace/models/NbAiLab_nb-whisper-large

hf download NbAiLabBeta/nb-whisper-large-semantic \
  --local-dir ~/workspace/models/NbAiLab_nb-whisper-large-semantic

accept this: 
https://huggingface.co/pyannote/speaker-diarization-community-1


export HF_TOKEN=xxxx
ffmpeg -i ~/workspace/files/dps_1.mp4 -ac 1 -ar 16000 -acodec pcm_s16le ~/workspace/files/dps_1.wav


whisperx ~/workspace/files/dps_1.wav \
--model ~/workspace/models/BuzzASR_norwegian-ct2 \
--language no \
--diarize \
--initial_prompt "Dette er en brukertest av webappen Kaia, som gir KI-støtte og kunstig intelligens for e-behandling ved DPS og mage-tarm-skolen. Testen foregår som en tenk-høyt-test der testeren navigerer på skjermen, bygger opp en kunnskapsbase og ser hvordan KI svarer basert på denne." \
--hf_token "<secret here>"


uv pip install "transformers[torch]"


ct2-transformers-converter \
  --model ~/workspace/models/BuzzASR_norwegian \
  --output_dir ~/workspace/models/BuzzASR_norwegian-ct2 \
  --copy_files tokenizer.json preprocessor_config.json \
  --quantization float16