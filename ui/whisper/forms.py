from django import forms


class WhisperForm(forms.Form):
    audio_file = forms.FileField(label='Audio file')
    model_name = forms.CharField(label='Model name', initial='golesheed/whisper-v2-7fold-1')
