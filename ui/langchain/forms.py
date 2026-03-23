from django import forms
from django.conf import settings


class NewSessionForm(forms.Form):
    model_name = forms.CharField(label='Naam model', initial=settings.DEFAULT_MODEL)


class MessageForm(forms.Form):
    message = forms.CharField(label='Bericht')
