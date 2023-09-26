import os
import json
import yaml
import time
import pyaudio
import collections
import keyboard
from pydub import AudioSegment
import openai
from dotenv import load_dotenv

from prompt import HEADER_PROMPTS

class AudioProcessor:
    def __init__(self, frame_rate=48000, frames_per_buffer=8192, buffer_duration=10, max_message_history=12, allow_history=False, print_transcript=False, trigger_key='right option'):
        """
        Arguments:
            frame_rate: Set to the Hz of your syste microphone (usually 48000 or 44100)
            frames_per_buffer: any reasonable and large int should work
            buffer_duration: N seconds to keep in the sliding context window
        """
        self.max_message_history = max_message_history
        self.allow_history = allow_history
        self.print_transcript = print_transcript
        self.trigger_key = trigger_key
        self.frame_rate = frame_rate
        self.frames_per_buffer = frames_per_buffer
        self.buffer_duration = buffer_duration
        self.buffer_size = (self.frame_rate // self.frames_per_buffer) * self.buffer_duration
        self.audio_buffer = collections.deque(maxlen=self.buffer_size)
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=self.frame_rate, input=True,
                                  frames_per_buffer=self.frames_per_buffer)
        self.user_triggered = False

        keyboard.hook_key(self.trigger_key, self.on_trigger)

        self.state = 'idle'

        # Prompt-engineering messages
        self.header_messages = HEADER_PROMPTS

        # User and GPT response messages
        if self.allow_history:
            self.messages = collections.deque(maxlen=self.max_message_history)
        else:
            self.messages = collections.deque(maxlen=1)

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

        self.handle_transcription(whisper_transcript)

        self.messages.append({"role": "user", "content": whisper_transcript})
        
        gpt_response = openai.ChatCompletion.create(
            model='gpt-4',
            messages = self.header_messages + list(self.messages)
        )

        gpt_response_text = gpt_response['choices'][0]['message']['content']
        self.messages.append({"role": "assistant", "content": gpt_response_text})
        
        self.handle_response(gpt_response_text)


    def transcribe_audio(self):
        """Send the audio data to Whisper API and get the transcript"""
        with open('buffer_audio.mp3', 'rb') as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
            return transcript.text

    def handle_response(self, text):
        """Do something with the response from GPT"""
        # Default: just print it out
        print(text)
    
    def handle_transcription(self, text):
        """Do something with the transcription from Whisper"""
        # Default: just print it out
        if self.print_transcript:
            print('\nYou:', text, '\n')


if __name__ == '__main__':
   
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")

    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    audio_processor = AudioProcessor(
        config['microphone_frequency'],
        config['microphone_frames_per_buffer'],
        config['audio_window_length'], 
        config['followup_question_window_size'], 
        config['allow_followup_questions'],
        config['print_whisper_transcript'],
        config['trigger_key']
    )

    audio_processor.run()
