"""Download encoder weights at Docker build time so runtime skips hub fetches.

Paths must stay in sync with adversarial_engine loaders and Dockerfile ENV.
"""

import os
from pathlib import Path

ECAPA_SAVEDIR = Path(
    os.environ.get(
        "SS_ECAPA_SAVEDIR",
        "pretrained_models/spkrec-ecapa-voxceleb",
    )
)


def main() -> None:
    print("Prefetching Resemblyzer...")
    from resemblyzer import VoiceEncoder

    VoiceEncoder(device="cpu")

    print("Prefetching ECAPA (SpeechBrain)...")
    from speechbrain.inference.speaker import EncoderClassifier

    ECAPA_SAVEDIR.mkdir(parents=True, exist_ok=True)
    EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        savedir=str(ECAPA_SAVEDIR),
    )

    print("Prefetching HuBERT...")
    from transformers import HubertModel

    HubertModel.from_pretrained("facebook/hubert-base-ls960")

    print("Model prefetch complete.")


if __name__ == "__main__":
    main()
