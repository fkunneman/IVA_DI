from typing import Dict
import requests
import base64

encoded = base64.b64encode(b'Hello World!')

class Api:
    def __init__(self):
        values: Dict[str, str] = {}
        with open('_SETTINGS', 'r') as settings:
            lines = settings.readlines()
            for l in lines:
                key, value = l.split('=', 1)
                values[key] = value.strip()
        self.values = values

    def _headers(self, response_type='application/json'):
        return {
            'Accept': response_type,
            'Authorization': 'Basic ' + base64.b64encode(f'{self.values['apiUser']}:{self.values['apiPassword']}'.encode('utf-8')).decode('ascii')
            }

    def start(self):
        """(Re)starts the session and returns the first message"""
        response = requests.post(
            self.values['startChainUrl'],
            '',
            headers=self._headers())

        print(response)
        data = response.json()
        self.agent_id = data['agent_id']
        return data['first_message']

    def message_lang_chain(self, text: str ) -> str:
        """Sends a text message to the lang chain and get a text response"""
        response = requests.post(
            self.values['messageChainUrl' + self.agent_id],
            f'message={text}',
            headers=self._headers())

        return response.json()['response']

    def speech2text(self, audio: bytes) -> str:
        response = requests.post(
            self.values['speechApiUrl'],
            files={'file', ('audio.wav', audio)},
            headers=self._headers('text')
        )
        return response
