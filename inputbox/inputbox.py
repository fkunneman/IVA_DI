#!/usr/bin/env python3
import asyncio
from multiprocessing import Queue, Manager
import multiprocessing
import time

from audio import SpeakSession

from inputs import get_gamepad
from led import set_leds, toggle_led, LED_BLUE, LED_GREEN, LED_RED, LED_YELLOW
from api import Api

PRIMARY_BUTTON_ID = "BTN_TRIGGER"
SECONDARY_BUTTON_ID = "BTN_THUMB"

listen_queue = Queue()
speak_queue = Queue()
agent_id_queue = Queue()
speak_session = SpeakSession()

running = True

manager = Manager()

api = Api()


class ExperimentSession:
    def __init__(self):
        self.__state = manager.Value("experiment_state", "preflight")
        """'preflight' | 'ready' | 'recording' | 'waiting' | 'error' | 'speaking'
        """
        self.agent_id = None

    def set_state(self, value):
        self.__state.set(value)

    def get_state(self):
        return self.__state.get()

    def start(self):
        """Starts a new session, aborts the current one if it's running"""
        self.stop()
        curr_state = self.get_state()
        match curr_state:
            case "recording":
                speak_session.stop_listening()

            case "speaking":
                speak_session.stop_saying()

        self.set_state("waiting")

        start_message, self.agent_id = api.start()

        agent_id_queue.put(self.agent_id)
        self.set_state("speaking")
        speak_queue.put(start_message)
        return self.agent_id

    def stop(self):
        agent_id = self.agent_id
        # clear it immediately; to prevent it from being removed
        # after a new agent ID was set
        self.agent_id = None
        if agent_id:
            api.stop(agent_id)
        else:
            print('Nothing to stop...')

    def press(self):
        """Changes the states on a button press"""
        curr_state = self.get_state()
        match curr_state:
            case "preflight":
                self.start()

            case "waiting":
                # show that nothing can be done now
                self.set_state("error")

            case "ready":
                self.listen()

            case "recording":
                # stop recording, the recording handler will process this
                self.set_state("waiting")
                speak_session.stop_listening()

            case "speaking":
                # abort speaking
                speak_session.stop_saying()
                self.listen()

        print(f"{curr_state} -> {self.__state.value} ")

    def listen(self):
        self.set_state("recording")
        listen_queue.put("")


experiment_session = ExperimentSession()


def button_target():
    # if the button is held for some time, also trigger after release
    start_press = time.time()

    while running:
        events = get_gamepad()
        for event in events:
            if event.ev_type == "Key" and event.code == PRIMARY_BUTTON_ID:
                if event.state == 1:
                    start_press = time.time()
                    experiment_session.press()
                elif event.state == 0 and (time.time() - start_press) > 1.0:
                    experiment_session.press()


def speak_target():
    while running:
        utterance = speak_queue.get()
        experiment_session.set_state("speaking")
        print(f'say "{utterance}"')
        if (
            speak_session.say(utterance)
            and experiment_session.get_state() == "speaking"
        ):
            experiment_session.set_state("ready")


def listen_target():
    while running:
        listen_queue.get()
        if not agent_id_queue.empty():
            agent_id = agent_id_queue.get()     
            print("AGENT_ID: " + agent_id)   

        recording = speak_session.listen()
        experiment_session.set_state("waiting")

        text = api.speech2text(recording)
        print(f'Text: {text}')
        response = api.message_lang_chain(text, agent_id)

        speak_queue.put(response)


def led_target():
    blink = False
    blink_speed = 0.4
    while running:
        curr_state = experiment_session.get_state()
        match curr_state:
            case "preflight":
                set_leds({LED_BLUE: True})

            case "ready":
                set_leds({LED_GREEN: True})

            case "recording":
                set_leds({LED_GREEN: blink, LED_BLUE: True})
                blink = not blink

            case "waiting":
                # reset the blink
                blink = False
                set_leds({LED_RED: True})

            case "error":
                blink_speed = 0.1
                set_leds({LED_RED: blink})
                blink = not blink

            case "speaking":
                set_leds({LED_YELLOW: True})

        if curr_state != "error":
            blink_speed = 0.4

        time.sleep(blink_speed)


def exit():
    global running
    print("Starting exit sequence")
    running = False

    for t in threads:
        t.terminate()


threads = [
    multiprocessing.Process(target=button_target),
    multiprocessing.Process(target=speak_target),
    multiprocessing.Process(target=listen_target),
    multiprocessing.Process(target=led_target),
]

for t in threads:
    t.start()

while running:
    command = input("Input command. Type 'h' for help\n> ")
    match command:
        case "h":
            print("""q\tQuit
r\tRestart""")
        case "q":
            experiment_session.stop()
            exit()
        case "r":
            experiment_session.start()
        case _:
            print("Not recognized press 'h' for help")

set_leds({LED_BLUE: True})
