from typing import Dict
import requests
import base64

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
        """(Re)starts the session and returns the first message and agent_id"""
        response = requests.post(
            self.values['startChainUrl'],
            '',
            headers=self._headers())

        if response.status_code != 200:
            print(response)

        data = response.json()
        agent_id = data['agent_id']
        return data['first_message'], agent_id

    def stop(self, agent_id: str):
        """Stops the active session"""
        response = requests.post(
            self.values['stopChainUrl'],
            {'session': agent_id},
            headers=self._headers())
        print(f"STOP SESSION: {response.status_code}")

    def message_lang_chain(self, text: str, agent_id: str) -> str:
        """Sends a text message to the lang chain and get a text response"""
        response = requests.post(
            self.values['messageChainUrl'] + agent_id,
            {
                'message': text
            },
            headers=self._headers())

        return response.json()['response']

    def speech2text(self, audio: bytes) -> str:
        with open('audio.wav', 'wb') as f:
            f.write(audio)

        response = requests.post(
            self.values['speechApiUrl'],
            files={'file': ('audio.wav', audio)},
            headers=self._headers('text')
        )
        return response.content.decode()
