# lockebot

![LockeBotLogo](media/JohnLockeLogoMini.jpg)

**LockeBot:** a demonstration of implementing a basic question answering bot with use of [Rasa NLU](https://github.com/golastmile/rasa_nlu) and a database.

## What is this?

It is a bot that can answer simple questions, via the terminal, email or [Let's Chat](http://sdelements.github.io/lets-chat/)

After being trained on examples, it is (to a degree) able to generalise the questions and respond to ones in a similar style. The questions are turned into intents and entities, which are then used to construct queries to run against a database to provide the answer.

Here is a demo of the BaseBot version (which is somewhat limited in what it can respond to and has a small table of people with some trivial characteristics, like name, number and location)

[![asciicast](https://asciinema.org/a/5j5zs42kk95itm1uzdqlwys86.png)](https://asciinema.org/a/5j5zs42kk95itm1uzdqlwys86)

This project grew out of my experiments to build a bot in Python using Rasa NLU. I should be up-front that this is not necessarily the perfect way to use it and there are probably many things that could be done in a more Pythonic way, but my intent is that by sharing it, others will either be able to get something basic working quickly or they'll use it for inspiration in another project.

Rasa NLU has the great advantage of letting you handle your NLU models locally and thus not hand off data to a third-party.  I'm not idealogically against use of third-party NLU tools, but when getting a sense of what is possible it seemed to me very useful not to require external involvement and I suspect others may be in this position too.

One other option with this project is to run the finished bot on a [Raspberry Pi](https://www.raspberrypi.org/).  Although you may well not wish to train the model on the Pi (it may take a rather long time!), once you have a trained model, it is very much capable of giving responses quickly and although large scale use will likely not be viable it works for small numbers of concurrent users (no testing on maximum numbers has been done, but email use with a group of ~20 users is definitely viable)

There is a **basebot** (which does very little) and a slightly more capable version **roybot** (which answers questions about English/British monarchs) 

## Install

Ensure you have Python 2.7 installed (it is not currently compatible with Python 3.n, see below)

For Raspberry Pi installation, there are a couple of changes to the steps for installing MITIE. See information under Additional installation choices below.

* Git clone from this repo
	* `git clone https://github.com/nmstoker/lockebot mybotfoldername` - *replace __mybotfoldername__ with any valid name you like*
	* `cd mybotfoldername`
* Create a virtual environment (optional but recommended)
	* `virtualenv2 venv` - *again you can use whatever name you like instead of __venv__ for your environment name*
* Activate the virtual environment
	* `source venv/bin/activate`
* Use pip install
	* `pip install requirements.txt`
* Manually install MITIE (*doesn't seem to work if included via requirements.txt even with "-e git+https://github.com/mit-nlp/MITIE.git" with or without #egg=...*)
	* `pip install git+https://github.com/mit-nlp/MITIE.git`
* Copy the feature_extractor files to MITIE folder
	* These instructions are simply the same as required by the backend set up steps for Rasa NLU under [Option 1 here](http://rasa-nlu.readthedocs.io/en/latest/backends.html)
	* Download the tar bzipped file from [here](https://github.com/mit-nlp/MITIE/releases/download/v0.4/MITIE-models-v0.2.tar.bz2)
	* Extract the contents temporarily and copy **total_word_feature_extractor.dat** into the **/MITIE** folder in sub-folders **/MITIE-models/english/**
	* You do not need the other files from the tar file
* Train models or copy existing ones into place
	* For training steps, see below (Usage) otherwise download the models from this Google Drive location:
	* https://drive.google.com/drive/folders/0B3K9eUuGgfbva2JUY2tYejc2ODg?usp=sharing
	* **/model_20170124-010214/** is required for BaseBot
	* **/model_20170210-024634/** is required for roybot
	* Save them in the '/models' folder of your local copy of the repo

If you simply wish to use the local terminal to work with the bot, you are ready to proceed to Usage.

But if you wish to use it via email or Let's Chat, see the addition requirements below.

### Additional installation choices

#### Raspberry Pi installation of MITIE


#### Let's Chat
Let's Chat has a variety of ways that it can be set up - for advice on that, please refer to the instructions in their repo's wiki [here](https://github.com/sdelements/lets-chat/wiki).  For development, I found docker very quick to get going with.  (NB: although LockeBot will work on a Raspberry Pi, no efforts have been made (yet!) to see if Let's Chat is viable on the Pi so I have no advice on that front)

Look at the script and find the constants for Let's Chat (all prefixed **LC_**) and update them as necessary to point to your particular Let's Chat instance. The primary one to focus on is **LC_BASE_URL** and this should correspond to a room in the Let's Chat where the bot will respond to questions from users. If you're running it locally you may be able to leave them "as is" if you create a room to match the default one ("base" for BaseBot).

In the bot script (eg basebot.py), edit **CHANNEL_IN** and **CHANNEL_OUT** to reference **'online'** and **'online': True** respectively (CHANNEL_IN can only take one value at a time, but CHANNEL_OUT can be true for **'screen'** and/or **'email'** as well as **'online'**) 

#### Email set up
To use LockeBot over email, it connects via IMAP and SMTP to an email account that you set up specifically for use with the bot.

Several major email services provide details the ability to connect with IMAP/SMTP - if this is not available for the email you wish to use, you will need to figure out how you can connect programmatically via Python (and re-write the necessary sections of code).

Dreamhost instructions for IMAP are here: https://help.dreamhost.com/hc/en-us/articles/215612887-Email-client-protocols-and-port-numbers

Gmail instructions for IMAP access are here: https://support.google.com/mail/answer/7126229?hl=en

Microsoft Outlook.com instructions for IMAP access are here: https://support.office.com/en-gb/article/Add-your-Outlook-com-account-to-another-mail-app-73f3b178-0009-41ae-aab1-87b80fa94970

If you are with another provider, check the details with them.

You need:
* Account username / password
* IMAP server name
* IMAP port #
* SMTP server name
* SMTP port #

It is possible the IMAP and SMTP hosts will match but if they differ, ensure you have them the right way around. Also if there are differences in relation to the standard ports, you would need to adjust this in the script (I plan to migrate this to an .ini setting shortly)

Simply update the details in the file `/config/settings.ini`. If you have problems, it is worth using another email client to ensure that you are definitely able to connect with the particular credentials you have.

In the bot script (eg basebot.py), edit **CHANNEL_IN** and **CHANNEL_OUT** to reference **'email'** and **'email': True** respectively (CHANNEL_IN can only take one value at a time, but CHANNEL_OUT can be true for **'screen'** and/or **'online'** as well as **'email'**) 

Email has not been tested with providers other than Dreamhost so far.

The script polls the email fairly frequently - you may find that a less frequent polling is wise but that does lead to longer delays before questions are responded to.  The use of IMAP "IDLE" commmands is not currently implemented (although it would be an obvious improvement).

## Usage

### Regular Bot Use

### Training

python -m rasa-nlu.train -c config/config.json

## Platforms
Currently it is only tested on **Linux** (specifically [Arch](https://www.archlinux.org/) x86-64 and [Raspbian](https://www.raspberrypi.org/downloads/raspbian/) on a Raspberry Pi 3)
In due course I would be interested like to support Windows and Mac - I have access to the former but not the latter, so if there's anyone keen to look into this on the Mac, volunteers will be gratefully received.

## Python versions
Whilst I would like to support Python 3.n, currently as Rasa NLU has a Python 2.7 dependency it is going to mirror that until support there is resolved.

## Technical background

## Roadmap

This project is a personal project that I've decided to open-source - whilst I would like it to work well for people, and am keen to make improvements to it, I am likely to have somewhat limited time in the near-term (H1 2017) so expect changes to be relatively slow (however don't be deterred from forking it if you like!)

* put in some tests!
* 

## Name origin
LockeBot gets its name from a terrible pun. It is built on Rasa NLU, and [John Locke](https://en.wikipedia.org/wiki/John_Locke) (the philospher) was notable for his work in relation to the empty slate arguments regarding the mind, called tabula rasa.

## Disclaimer
I am very grateful for the various tools which make this small project possible, however I should make clear that this software is not endorsed by any of the email providers mentioned above, Let's Chat, nor LastMile (producers of Rasa NLU).
