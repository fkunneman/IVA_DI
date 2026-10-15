from multiprocessing import Manager
from piper import PiperVoice
import pyaudio
import wave
import io

voice = PiperVoice.load("./piper_models/nl_NL-alex-medium.onnx")

# how many bytes are streamed at once?
# every time a poll is done to see if the streaming should be aborted
STREAM_WINDOW = 1000

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 512

manager = Manager()

class SpeakSession:
    utterance_index = 0
    abort_listening = manager.Value('abort_listening', False)

    """Keeps track of the current utterance.
    If an utterance is skipped, this is how it can be done
    """

    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None

    def say(self, utterance: str):
        self.stop_listening()
        self.utterance_index += 1
        current_utterance_index = self.utterance_index

        for chunk in voice.synthesize(utterance):
            if self.stream is None:
                self.stream = self.audio.open(
                    format=self.audio.get_format_from_width(chunk.sample_width),
                    channels=chunk.sample_channels,
                    rate=chunk.sample_rate,
                    output=True,
                )

            for subchunk in range(0, len(chunk.audio_int16_bytes), STREAM_WINDOW):
                # stop streaming the utterance
                if self.utterance_index != current_utterance_index:
                    return

                self.stream.write(
                    chunk.audio_int16_bytes[subchunk : subchunk + STREAM_WINDOW]
                )

    def stop_saying(self):
        """Stop speaking right now"""
        self.utterance_index += 1

    def listen(self):
        self.stop_saying()
        self.abort_listening.set(False)

        stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )

        frames = []

        try:
            while not self.abort_listening.get():
                data = stream.read(CHUNK)
                frames.append(data)
        finally:
            stream.stop_stream()
            stream.close()

        wave_bytes = io.BytesIO()
        with wave.open(wave_bytes, "wb") as wav_file:
            wav_file.setnchannels(CHANNELS)
            wav_file.setsampwidth(self.audio.get_sample_size(FORMAT))
            wav_file.setframerate(RATE)
            wav_file.writeframes(b"".join(frames))
            wav_file.close()

        wave_bytes.seek(0)
        return wave_bytes.read()

    def stop_listening(self):
        self.abort_listening.set(True)

    def __exit__(self, exc_type, exc, tb):
        if self.stream is not None:
            self.stream.close()
        self.audio.terminate()
