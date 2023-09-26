# Setup (macOS)

### preliminaries

0.1 Install python 3.11+  

0.2 Install homebrew

0.3 Make an OpenAI account, if you do not have one already

0.4 Create an OpenAI API key here: https://platform.openai.com/account/api-keys

0.5 Copy your OpenAI API key to the clipboard, then add it to a new file called `.env` by running the following in the terminal: `echo "OPENAI_API_KEY=your_openai_api_key" > .env`

### installations with `brew`

1.1 Install `portaudio` by running the following in the terminal: `brew install portaudio`  

1.2 Install `ffmpeg` by running the following in the terminal: `brew install ffmpeg`  

### virtual environment

2.1 Create a virtual environment by running the following in the terminal: python3.11 -m venv venv

2.2 Activate the virtual environment: source venv/bin/activate

2.3 Install the dependencies: pip install -r requirements.txt

# Usage

To run the program, open the terminal, navigate to the directory containing the main python file and your .env file. (Note: the .env file will not be visible in the Finder by default. To confirm its presence after creating it (step 0.5), run `ls -a` in the terminal, or press Cmd+Shift+. (period) in Finder. It should have a single line of text: `OPENAI_API_KEY="your key here"`

Once in the correct location, in the Terminal, make sure the environment is active (run `source/venv/bin/activate`), then run the following: `sudo python starter_code.py`

This will prompt you for your password, which is required in order to access the computer's keyboard and microphone. The program will then be live. You can speak, and if at any point you press the Right Option key on the keyboard, the last ten seconds of audio captured by the microphone will be processed first by OpenAI's Whisper model, then by GPT-4. The answer to your "question" posed in those last ten seconds of speech will then be printed in the terminal.

Note that, currently, this application does not support follow-up questions. That is, a new call to the GPT-4 endpoint is made with each press of the Right Option key, and previous messages are not included in this call. 

Note further that no data is being saved or sent to any APIs except for the last ten seconds of audio only when the Right Option key is pressed. That is, there is no harm in leaving this program running in the background, since it will not use excess memory or make any API calls until the trigger key is pressed. Although, it would probably be wise to close it when you plan to be done using it, so as to avoid unintentionally sending API requests.
