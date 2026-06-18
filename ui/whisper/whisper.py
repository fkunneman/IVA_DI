from pathlib import Path

from django.conf import settings
import torch
from transformers import pipeline
from murmel import Murmel


pipelines = {}


def transcribe(model_name: str, audio_file: Path | str, follow_override_setting=True) -> str:
    if follow_override_setting and hasattr(settings, "OVERRIDE_MODEL"):
        model_name = settings.OVERRIDE_MODEL

    if model_name == "murmel" and hasattr(settings, "MURMEL_API_KEY"):
        # Instead of using the local model, use the Murmel API
        client = Murmel(api_key=settings.MURMEL_API_KEY)
        result = client.transcribe(str(audio_file), language="nl")
        return result.text

    if model_name not in pipelines:
        pipeline_ = pipeline("automatic-speech-recognition", model=model_name, dtype=torch.float16, device=settings.DEVICE, return_timestamps=True)
        pipelines[model_name] = pipeline_
    else:
        pipeline_ = pipelines[model_name]

    result = pipeline_(str(audio_file))
    return result["text"]

