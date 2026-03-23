from pathlib import Path

from django.conf import settings
import torch
from transformers import pipeline


pipelines = {}


def transcribe(model_name: str, audio_file: Path | str) -> str:
    if model_name not in pipelines:
        pipeline_ = pipeline("automatic-speech-recognition", model=model_name, dtype=torch.float16, device=settings.DEVICE, return_timestamps=True)
        pipelines[model_name] = pipeline_
    else:
        pipeline_ = pipelines[model_name]

    result = pipeline_(str(audio_file))
    return result["text"]

