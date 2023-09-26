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
    def __init__(self, frame_rate=48000, frames_per_buffer=8192, buffer_duration=10, max_message_history=12, allow_history=False, print_transcript=False, trigger_key='right option', model='gpt-3.5-turbo'):
        """
        Initializes an instance of the AudioProcessor class, setting up the environment for recording and processing audio, managing conversation history, and handling user interaction triggers.

        Arguments:
            frame_rate (int, optional): Represents the sample rate of the audio signal. Typically set to the Hz of the system microphone (usually 48000 or 44100). Defaults to 48000.
            frames_per_buffer (int, optional): Size of the buffer to hold audio frames. A reasonable and large int should be sufficient. It determines how many frames are processed at a time. Defaults to 8192.
            buffer_duration (int, optional): Determines the duration in seconds to keep in the sliding context window, i.e., the amount of audio data to retain. Defaults to 10.
            max_message_history (int, optional): Maximum number of messages to keep in history when allow_history is True. Defaults to 12.
            allow_history (bool, optional): Flag to decide whether to allow message history or not. If True, AudioProcessor instance will keep a history of messages up to max_message_history. Defaults to False.
            print_transcript (bool, optional): If True, prints the transcript obtained from the audio. Useful for debugging and monitoring. Defaults to False.
            trigger_key (str, optional): Specifies the key to be used as a trigger for processing audio. Defaults to 'right option'.
            model (str, optional): Specifies the model to be used for processing, e.g., 'gpt-3.5-turbo'. Defaults to 'gpt-3.5-turbo'.

        Attributes:
            model (str): Specifies the model used for processing, can be set to different versions like 'gpt-3.5-turbo'.
            max_message_history (int): Specifies the maximum number of messages to store when 'allow_history' is set to True.
            allow_history (bool): Determines whether to store the history of messages up to 'max_message_history'.
            print_transcript (bool): A flag that, when True, triggers the printing of the transcript to the console. Useful for debugging purposes.
            trigger_key (str): Represents the key assigned as the trigger for processing audio, such as 'right option'.
            frame_rate (int): Represents the sample rate of the audio signal, typically 48000 or 44100 Hz, used in setting up the audio stream.
            frames_per_buffer (int): The size of the buffer holding audio frames, determining how many frames are processed at once during audio stream read.
            buffer_duration (int): Represents the duration in seconds of the audio data to retain in the sliding context window.
            buffer_size (int): Calculated size of the buffer used to store audio data, based on 'frame_rate' and 'frames_per_buffer'.
            p (pyaudio.PyAudio): Instance of the PyAudio class, used to interact with and manipulate the system's audio functionalities.
            stream (pyaudio.Stream): Represents the audio stream object from which data is read, set up with the specified 'frame_rate', 'frames_per_buffer', and other audio parameters.
            user_triggered (bool): Flag indicating whether the user has triggered the audio processing, typically by pressing the 'trigger_key'.
            state (str): Current state of the AudioProcessor instance, used to manage the flow and functionalities of the processor. Initially set to 'idle'.
            header_messages (list): List containing pre-defined header prompts or prompt-engineering messages, used during interactions with the model.
            messages (collections.deque): A deque object holding the history of user and model response messages, with its maximum length set by 'max_message_history' if 'allow_history' is True, otherwise set to 1.
        """
        
        self.model=model
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
            model=self.model,
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
        config['trigger_key'],
        config['model']
    )

    audio_processor.run()
