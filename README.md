# Overview

This is a tool in development that lets you use your voice to communicate with GPT models. Rather than having to first tell the model to listen, and only then ask your question, this tool is always listening. Triggering it causes the model to analyze the last `n` seconds of audio captured by the microphone. 

This removes the redundancy and interruption of having to, for instance, say "Hey, Siri," or "Okay, Google", before asking your question. For example, suppose you were having a conversation at dinner, and it got to a point where you weren't sure how to proceed without looking something up. Instead of having to say "Hey, Alexa," and then repeat or restate the question, you could just say "Hey Alexa, what do you think about that?" 

This is a small step in that direction: The assumption is that the audio is always there, being recorded, and all you have to do is trigger the processing pipeline when you want it to be analyzed.

By default, this tool is steered toward concise responses. It expects to receive questions that may be incomplete or may lack sufficient context. The idea is that a professor could have this tool running in the background during their lecture, and when presented with a question they don't know how to answer, could simply trigger the tool and read the answer it provides. 

For example, suppose I didn't know that the capital of California was Sacramento. If you asked me, "What's the capital of California", I could quickly press the button on my system to trigger the model to start processing that last audio snippet, which contained your question. I could then start speaking, saying, "the Capital of California is", by which time the model will have spit out its result, "Sacramento."

# Setup (macOS)

### preliminaries

0.1 Install python 3.11+  

0.2 Install homebrew

0.3 Make an OpenAI account, if you do not have one already

0.4 Create an OpenAI API key here: https://platform.openai.com/account/api-keys

0.5 Copy your OpenAI API key to the clipboard, then add it to a new file called `.env` by running the following in the terminal: `echo "OPENAI_API_KEY=your_openai_api_key" > .env`, replacing `your_openai_api_key` with the key you copied.

### installations with `brew`

1.1 Install `portaudio` by running the following in the terminal: `brew install portaudio`  

1.2 Install `ffmpeg` by running the following in the terminal: `brew install ffmpeg`  

### virtual environment

2.1 Create a virtual environment by running the following in the terminal: python3.11 -m venv venv

2.2 Activate the virtual environment: source venv/bin/activate

2.3 Install the dependencies: pip install -r requirements.txt

# Usage

Open the terminal and navigate to the directory containing 
the main python file and your `.env` file. (Note: the .env file will not be 
visible in the Finder by default. To confirm its presence after creating 
it (which you did in step 0.5), run `ls -a` in the terminal, or press Cmd+Shift+. (Command 
shift period) in the Finder. The .env file should have a single line of text: 
`OPENAI_API_KEY=your_key_here`. You can confirm this in the terminal by running `cat .env`. 

Once in the correct location in the terminal, make sure the virtual environment is active (run `source/venv/bin/activate`), then run the following command to run the program: `sudo python run.py`

The first time you run the program, it may ask you to turn on Accessibility permissions. You will have to open System Preferences and toggle the switch for the application running the program (typically the Terminal). If it crashes (`Segfault`, `Error`, similar), try restarting it with the same command again: `sudo python run.py`. 

Because the program needs access to your keyboard and microphone, it must be run in administrator mode, which is why you place `sudo` before `python` in the run command. When running as an administrator for the first time, the program will prompt you for your password. This is the same password you use to log into your computer when it restarts.

Once the permissions are set and you enter your password, the program will be live. You can speak, or even whisper, to communicate with it. If at any point you press the Right Option key on the keyboard, the last ten seconds (or more -- this is configurable in the `config.yaml` file) of audio captured by the system microphone will be processed first by OpenAI's Whisper model (to go from speech to text), then by GPT (to respond to what you said). The response from GPT will be printed out in the terminal.

Note that, by default, this application does not support follow-up questions. That is, a new call to the GPT API endpoint is made with each press of the Right Option key, and previous messages are not included in this call. However, you can enable follow-up questions, and configure the chat history (context window) used, in the `config.yaml` file.

Note further that no data is being saved, or sent to any APIs, except for the last ten seconds of audio only when the Right Option key is pressed. That is, there is no harm in leaving this program running in the background, since it will not use excess memory or make any API calls until the trigger key (Right Option) is pressed. That said, it would probably be wise to close it when you plan to be done using it, so as to avoid unintentionally sending API requests.

# Customization

The easiest way to customize your use of this tool is with the `config.yaml` file. Here you can toggle chat history, which changes the behavior of the system. By default, this means that each time you press the trigger key, it is as if you started a new chat with ChatGPT. Specifically, this means that if you ask it, "Who is the best band from the UK?", and it responded with "Radiohead", and then you asked it "What is the last question I asked you?" it would not know.

However, by changing `allow_followup_questions` to `true` in the `config.yaml` file, it would know what you're talking about. The last 12 messages (by default, also configurable) are saved. Each exchange (one message from you + one response from GPT) counts as two messages, so essentially it will remember 6 questions back. If you want to increase this number, you can change the `followup_question_window_size` parameter in the `config.yaml` file.

Another way to change the behavior of the tool is to toggle on the `print_whisper_transcript` parameter in the `config` file. This will let you see what, exactly, the Whisper model interpreted you as saying. 

For more advanced customization, you can edit the header prompts in the `prompt.py` file. These are the messages that get sent to the model every time, no matter how many messages you have acculumated or whether you have chat history turned on. The first of these is a `system` prompt. This has the most sway over the behavior of the model. By default, this system prompt tells the model to be very concise. The idea is that the model could be whispering in your ear, and you would be able to say what it says, without people thinking twice about it. Obviously, if the model always started its responses with a bunch of LLM preamble, like "As a Large Language Model developed by OpenAI, blah blah...", this wouldn't work.

If you are less interested in the "earbud" application, and instead want to have a casual converation with the model, or use it more like standard ChatGPT, just with speech-to-text, you could rewrite the `system` prompt to be simpler: something like "You are a helpful assistant". You would then probably also want to remove the two subsequent "example" messages, which are there for further alignment.

# Extensibility

At the heart of this program is the `AudioProcessor` class, defined and used in `run.py`. By default, once the audio (your speech) has been processed first by Whisper and then by the GPT model of your choice (configured in `config.yaml`), and the response from the GPT model has been obtained, that text just gets printed out. But it doesn't have to stop there. By adding logic to the `handle_response()` method of the `AudioProcessor` class, you could, for example, pass that response text off to a text-to-speech API, obtain a temporary audio file with the spoken version of the GPT response, and route that audio into an earbud you're wearing. The possibilities are endless.