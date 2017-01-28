LOGO

Lead sentence: LockeBot: a demonstration of implementing a basic question answering bot with use of Rasa NLU and a database.

#What is this?

[image of LockeBot in use]

This project grew out of my experiments to build a bot in Python using Rasa NLU. I should be up-front that this is not necessarily the perfect way to use it and there are probably many things that could be done in a more Pythonic way, but my intent is that by sharing it, others will either be able to get something basic working quickly or they'll use it for inspiration in another project.

Rasa NLU has the great advantage of letting you handle your NLU models locally and thus not hand off data to a third-party.  I'm not idealogically against use of third-party NLU tools, but when getting a sense of what is possible it seemed to me very useful not to require external involvement and I suspect others may be in this position too.

One other option with this project is to run the finished bot on a Raspberry Pi.  Although you may well not wish to train the model on the Pi (it may take a rather long time!), once you have a trained model, it is very much capable of giving responses quickly and although large scale use will likely not be viable it works for small numbers of concurrent users (LIMITS NOT TESTED, but email use with a group of ~20 users is definitely viable)

#Installation

- git clone from this repo
	FILL IN INSTRUCTIONS
- create virtual environment
	virtualenv2 venv
- activate virtual environment
	source venv/bin/activate
- pip install
	pip install requirements.txt
- copy the feature_extractor files to MITIE folder
	STEPS FOR DOWNLOADING
	EXTRACTING TO CORRECT FOLDER

#Platforms
Currently it is only tested on Linux (specifically Arch x86-64 and Raspbian on a Raspberry Pi 3)
In due course I would be interested like to support Windows and Mac - I have access to the former but not the latter, so if there's anyone keen to look into this on the Mac, volunteers will be gratefully received.

#Python versions
Whilst I would like to support Python 3.n, currently as Rasa NLU has a Python 2.7 dependency it is going to mirror that until support there is resolved.

#Technical background

#Roadmap

This project is a personal project that I've decided to open-source - whilst I would like it to work well for people, I am likely to have limited time in the near-term (H1 2017) so expect changes to be relatively slow (however don't be deterred from forking it if you like!)

- put in some tests!
- 

#Name origin
LockeBot gets its name from a terrible pun. It is built on Rasa NLU, and John Locke (the philospher) was notable for his work in relation to the empty slate arguments regarding the mind, called tabula rasa.
