#!/usr/bin/env python3
import asyncio
from multiprocessing import Queue, Manager
import multiprocessing
import time

from audio import SpeakSession

from inputs import get_gamepad
from led import set_leds, toggle_led, LED_BLUE, LED_GREEN, LED_RED, LED_YELLOW

PRIMARY_BUTTON_ID = "BTN_TRIGGER"
SECONDARY_BUTTON_ID = "BTN_THUMB"

listen_queue = Queue()
speak_queue = Queue()
speak_session = SpeakSession()

running = True

manager = Manager()


class ExperimentSession:
    def __init__(self):
        self.__state = manager.Value("experiment_state", "preflight")
        """'preflight' | 'ready' | 'recording' | 'waiting' | 'speaking'
        """

    def set_state(self, value):
        self.__state.set(value)

    def get_state(self):
        return self.__state.get()

    def start(self):
        """Starts a new session, aborts the current one if it's running"""
        curr_state = self.get_state()
        match curr_state:
            case "recording":
                speak_session.stop_listening()

            case "speaking":
                speak_session.stop_saying()

        self.set_state("waiting")

        # TODO: start session and retrieve start message
        self.set_state("speaking")
        speak_queue.put(
            "Hallo, welkom bij het begin van dit onderzoek. We doen alsof dit het juiste startbericht is."
        )

    def press(self):
        """Changes the states on a button press"""
        curr_state = self.get_state()
        match curr_state:
            case "preflight":
                self.start()

            case "waiting":
                pass

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
    global speak_queue

    while running:
        events = get_gamepad()
        for event in events:
            if event.ev_type == "Key":
                if event.state == 1 and event.code == PRIMARY_BUTTON_ID:
                    experiment_session.press()


def speak_target():
    while running:
        utterance = speak_queue.get()
        experiment_session.set_state("speaking")
        print(f'say "{utterance}"')
        speak_session.say(utterance)
        experiment_session.set_state("ready")


def listen_target():
    while running:
        listen_queue.get()
        recording = speak_session.listen()
        print(len(recording))
        # TODO: send recording to server
        experiment_session.set_state("waiting")
        time.sleep(2)
        speak_queue.put("Hallo wereld, dit zou het antwoord zijn.")


def led_target():
    blink = False
    while running:
        match experiment_session.get_state():
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

            case "speaking":
                set_leds({LED_YELLOW: True})

        time.sleep(0.4)


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
            exit()
        case "r":
            experiment_session.start()
        case _:
            print("Not recognized press 'h' for help")

set_leds({LED_BLUE: True})
