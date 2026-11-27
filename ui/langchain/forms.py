from django import forms
from django.conf import settings

from .agents import agents


class NewSessionForm(forms.Form):
    model_name = forms.CharField(label='Naam model', initial=settings.DEFAULT_MODEL, disabled=True)


class MessageForm(forms.Form):
    message = forms.CharField(label='Bericht')


def get_session_choices():
    return ((x, x) for x in agents.keys())


class SessionsForm(forms.Form):
    session = forms.ChoiceField(choices=get_session_choices)
