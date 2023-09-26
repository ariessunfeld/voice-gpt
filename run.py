import os
import json
import time
import pyaudio
import collections
import keyboard
from pydub import AudioSegment
import openai
from dotenv import load_dotenv

#print(keyboard._canonical_names.canonical_names)


class AudioProcessor:
    def __init__(self, frame_rate=48000, frames_per_buffer=8192, buffer_duration=10):
        """
        Arguments:
            frame_rate: Set to the Hz of your syste microphone (usually 48000 or 44100)
            frames_per_buffer: any reasonable and large int should work
            buffer_duration: N seconds to keep in the sliding context window
        """
        self.frame_rate = frame_rate
        self.frames_per_buffer = frames_per_buffer
        self.buffer_duration = buffer_duration
        self.buffer_size = (self.frame_rate // self.frames_per_buffer) * self.buffer_duration
        self.audio_buffer = collections.deque(maxlen=self.buffer_size)
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=self.frame_rate, input=True,
                                  frames_per_buffer=self.frames_per_buffer)
        self.user_triggered = False
        keyboard.hook_key('right option', self.on_trigger)

        self.state = 'idle'

    def on_trigger(self, e):
        """Callback function to detect the trigger key"""
        self.user_triggered = True

    def run(self):
        """Main loop of the audio processer"""

        # Initial state when starting to run
        self.state = 'recording'

        while True:

            if self.state == 'recording':

                try:
                    data = self.stream.read(self.frames_per_buffer)
                    self.audio_buffer.append(data)
                except IOError:
                    print("Buffer overflow, data may be lost!")
                    continue # Could do self.state = 'exit' here instead

                # Jump out and process data if trigger key is pressed
                if self.user_triggered:
                    self.handle_trigger_event()
                    self.user_triggered = False  # Reset the trigger
                    self.state = 'idle'  # Change state to idle after processing

            elif self.state == 'idle':

                # Can do whatever here; currently set up to restart recording

                # Reset the audio stream components
                self.audio_buffer = collections.deque(maxlen=self.buffer_size)
                self.p = pyaudio.PyAudio()
                self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=self.frame_rate, input=True,
                                        frames_per_buffer=self.frames_per_buffer)

                # Change state back to 'recording'
                self.state = 'recording'

            elif self.state == 'exit':

                break  # Exit the loop and end the program

    def handle_trigger_event(self):
        """Write the audio buffer down as mp3"""
        audio_bytes = b''.join(self.audio_buffer)
        audio_segment = AudioSegment(data=audio_bytes, sample_width=2, frame_rate=self.frame_rate, channels=1)
        audio_segment.export("buffer_audio.mp3", format="mp3")
        
        whisper_transcript = self.transcribe_audio()
        
        gpt_response = openai.ChatCompletion.create(
            model='gpt-4',
            messages = [
                {"role": "system", "content": "You are a helpful assistant. You try to give short and accuracte answers to technical questions, even when the questions lack context. You do not include preamble in your responses; you just respond with the answer to the question being asked."},
                {"role": "user", "content": "I am going to be sending you transcriptions of short audio snippets of my speech. In these transcriptions, I will usually be repeating a question that was just asked of me. I want you to try to answer the questions I pose as concisely and accurately as possible, so that I could easily continue saying what I was just saying and follow it up with your answer and it would seem like natural speech. Are you ready?"},
                {"role": "assistant", "content": "Yes, I am ready. Please send me the first question, and I will respond consicely and accurately respond so that you could follow up with my response and it would sound natural."},
                {"role": "user", "content": whisper_transcript}
            ]
        )

        print(gpt_response['choices'][0]['message']['content'])


    def transcribe_audio(self):
        """Send the audio data to Whisper API and get the transcript"""
        with open('buffer_audio.mp3', 'rb') as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
            return transcript.text


if __name__ == '__main__':
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    audio_processor = AudioProcessor()
    audio_processor.run()
