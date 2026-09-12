# text to audio

https://huggingface.co/ACE-Step/acestep-v15-xl-turbo

https://huggingface.co/ACE-Step/acestep-v15-xl-sft

https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/ace_step_musicians_guide.md

## system prompt

The prompt compiler should output ACE-native planning inputs, not prose.

Preferred payload:

```json
{
	"prompt": "cyberpunk, darksynth, male vocal, aggressive, neon city, distorted bass, analog arpeggiator, cinematic, futuristic, tense, glitch textures",
	"lyrics": "[Verse]\nNeon lights are burning through the rain\n\n[Chorus]\nHack the mainframe, break the silence",
	"duration": 180,
	"bpm": 118,
	"keyscale": "A minor",
	"timesignature": "4/4",
	"language": "en"
}
```

Notes:

- `prompt` is the ACE caption: style, mood, timbre, instruments, vocal type, production style.
- `lyrics` is the temporal script: sections, vocal behavior, and instrumental evolution.
- Use metadata fields for exact controls like tempo, key, meter, duration, and language.
- Keep `prompt` compact and high-signal; keep `lyrics` structurally clear.

## gemma4 + smaller ace lm

If Gemma4 is doing the prompt parsing and metadata planning, ACE can usually run with a smaller planner LM or no LM at all.

- Gemma4 replaces most of the planning work.
- ACE still keeps its own core text-conditioning path for audio generation.
- Practical options to test are: no ACE LM, ACE 0.6B LM, or ACE 1.7B LM.
- Start with no ACE LM or 0.6B LM and compare quality with a fixed seed.

## per-request lm bypass

If you want to keep the ACE LM installed but skip it for one generation, disable the LM planning features on that request:

```json
{
	"thinking": false,
	"use_cot_metas": false,
	"use_cot_caption": false,
	"use_cot_language": false
}
```

This is the practical "Gemma4 does the planning, ACE just generates" mode.

- Keep ACE's LM available for other runs.
- Skip metadata inference, caption rewrite, and language detection for this request.
- Feed ACE the full payload from Gemma4: `prompt`, `lyrics`, `duration`, `bpm`, `keyscale`, `timesignature`, and `language`.
 