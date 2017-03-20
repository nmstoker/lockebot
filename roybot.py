# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import signal
import os
import random
import time
import arrow
import readline
import logging
from colored import fore, back, style
import click

import json
import sqlite3
import requests
import roman
from rasa_nlu.interpreters.mitie_interpreter import MITIEInterpreter
# import imaplib
# import smtplib
# import email
# from email.MIMEMultipart import MIMEMultipart
# from email.MIMEText import MIMEText
import ConfigParser
import re
## from collections import defaultdict
## import string
from string import Template
import util as u # some local utility functions

# def open_connection():
#     """Opens the connection to the email service by use of the stored
#     credentials"""

#     # TODO: find a more sensible and secure approach or at least recommend
#     # securing the credential file and add handling in the event of being
#     # unable to read it.

#     # Read the config file
#     config = ConfigParser.ConfigParser()
#     config.read([os.path.abspath(os.path.join('config', 'settings.ini'))])

#     # Connect to the server
#     hostname = config.get('server', 'imap-hostname')
#     self.logger.debug('Connecting to ' + hostname)
#     connection = imaplib.IMAP4_SSL(hostname, 993)

#     # Login to our account
#     username = config.get('account', 'username')
#     password = config.get('account', 'password')
#     self.logger.debug('Logging in as ' + username)
#     connection.login(username, password)
#     return connection


# def get_msgs(subject=botname):
#     """Gets all the messages that are unseen, with part of the subject matches
#     the supplied subject (which defaults to be the bot name (botname)"""

#     self.logger.debug('Checking messages')
#     conn = open_connection()
#     conn.select('INBOX')
#     typ, data = conn.search(None, '(UNSEEN SUBJECT "%s")' % subject)
#     for num in data[0].split():
#         typ, data = conn.fetch(num, '(RFC822)')
#         msg = email.message_from_string(data[0][1])
#         typ, data = conn.store(num, 'FLAGS', '\\Seen')
#         yield msg
#     self.logger.debug('Logging out')
#     conn.logout()


# def get_sender(msg):
#     """Trivial helper function to get the sender from an email message"""
#     return msg['From']


# def get_email_addr(sender):
#     """Gets the pure email address (eg 'jdoe@example.com') from a sender
#     (eg 'John Doe <jdoe@example.com') using a simplified regular expression"""

#     # TODO: test how effective this is and whether there are many/any cases
#     #      where it doesn't work
#     expr = re.compile(r'[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}')
#     return expr.findall(sender)[0]


# def get_body(msg):
#     """Gets the email body of a specified email message."""
#     for part in msg.walk():
#         if part.get_content_type() == "text/plain":
#             body = part.get_payload(decode=True)
#             return body.decode('utf-8')
#         else:
#             continue


# def download_emails():
#     """Obtains the new emails received by the email account configured for
#     the bot, filtering to only respond to those sent by users on the safe list.
#     An additional degree of basic filtering happens in the get_msgs function
#     (eg to focus on new items with specific subject."""

#     # CUSTOMISE: this can be left "as is" but if your bot has more involved
#     # needs for exactly how it responds and to whom, then a re-write may be
#     # needed.
#     #
#     # There is currently nothing present to allow following a conversation
#     # 'thread' either, so each interaction is a one off with no concept of
#     # prior conversation or information provided (so that may need to be added)

#     self.logger.info('Checking emails')
#     safe_list = ['example1@example.com', 'example2@example.com']
#     lst = []
#     for msg in get_msgs():
#         sender = get_email_addr(get_sender(msg))
#         if sender in safe_list:
#             self.logger.debug('Email from: ' + sender)
#             user_input = get_body(msg).split('\n')[0][:100]
#             self.logger.debug('With first line: ' + user_input)
#             lst.append({'user_input': user_input, 'sender': sender})
#     return lst

# def store_email(mail_text):
#     """Specifically logs the email content sent, as this is a potentially
#     richer source than the basic intent history alone and it can be useful to
#     retain who the recipient was as well."""
#     with open(email_output_file, "a") as f:
#         f.write(str(mail_text) + '\n')


# def send_email(address='test@example.com'):
#     """Sends email via the configured email account to the address specified
#     (with a fall-back of a safe non-end-user supplied email the default for
#     'address'). Currently works with several globals (not ideal!)"""

#     # TODO: fix this to not use globals (urggh!)
#     global email_text
#     global email_subject
#     if not email_text.strip() == '':
#         # Read the config file
#         config = ConfigParser.ConfigParser()
#         config.read([os.path.abspath('settings.ini')])

#         # Connect to the server
#         hostname = config.get('server', 'smtp-hostname')
#         self.logger.debug('Connecting to ' + hostname)
#         server = smtplib.SMTP(hostname, 587)
#         server.ehlo()

#         # Login to our account
#         username = config.get('account', 'username')
#         password = config.get('account', 'password')
#         self.logger.debug('Logging in as ' + username)

#         server.starttls()
#         server.ehlo()
#         server.login(username, password)

#         fromaddr = username
#         toaddr = address
#         msg = MIMEMultipart()
#         msg['From'] = fromaddr
#         msg['To'] = toaddr
#         msg['Subject'] = email_subject
#         msg.attach(MIMEText(email_text, 'plain', 'utf-8'))

#         store_email(
#             '----------\nTo: ' + address + '\nSubject: ' + email_subject +
#             '\nContent:\n' + email_text)

#         server.sendmail(username, [address], msg.as_string())
#         server.quit()

#         email_text = STY_EMAIL + 'EMAIL' + STY_USER + '\n' + msg.as_string()
#         print(email_text)

#     email_text = ''
#     email_subject = ''




class Core:
    """Core is the main class for RoyBot"""

    def map_feature_to_field(self, feature):
        """Takes a feature string and returns a list of the corresponding
        database fieldname(s) (usually just one but can handle more)"""

        # -------------------------------------------------------------------------
        # CUSTOMISE THIS TO PURPOSE OF THIS BOT
        # -------------------------------------------------------------------------
        #
        # Used where a feature is to be mapped to a database field.
        #
        # Not strictly required but if the user's input is allowed to vary from a
        # narrow range of precise words then something like this will be necessary.
        #
        # This is a hard-coded approach and there are other ways it could be done,
        # but it is largely a trade off between accuracy and flexibility
        #
        # -------------------------------------------------------------------------

        self.logger.debug('Feature to map: ' + feature)

        f = feature.lower()

        # NB: this structure assumes all features will be mapped by at least one of
        # the conditions below; if you have acceptable features that should be
        # passed through then some slight changes to the logic would be needed.

        if f in ('events'):
            return ['NotableEventsDuringLife']
        if f in ('describe', 'description', 'brief description', 'about'):
            return ['Description']
        if f in ('born', 'birth'):
            return ['DtBirth']
        if f in ('die', 'died', 'death'):
            return ['DtDeath']
        if f in ('king from','queen from', 'reign from', 'reign begin', 'reign began', 'started', 'become', 'rule from', 'rule start', 'rule began'):
            return ['ReignStartDt']
        if f in ('king until','queen until', 'reign until', 'reign to', 'reign end', 'reign ended', 'end', 'become', 'rule until'):
            return ['ReignEndDt']
        if f in ('cause of death', 'killed'):
            return ['DeathCircumstances']
        if f == 'house':
            return ['House']
        if f in ('portrait', 'picture', 'look', 'painting'):
            return ['Portrait']
        if f == 'title':
            return ['Title']
        if f in ('country', 'where'):
            return ['Country']
        if f in ('battle', 'battles', 'famous battles', 'wars', 'war', 'fight', 'fought'):
            return ['FamousBattles']
        if f in ('person', 'individual'):
            return ['Name']
        if f == 'number':
            return ['Number']
        if f in ('all', 'about'):
            return ['Name', 'Number', 'DtBirth', 'DtDeath', 'ReignStartDt', 'ReignEndDt', 'FamousBattles', 'Description']
        # so we didn't match anything
        return []


    def map_entity_to_number(self, ent):
        """Takes a complete entity and returns the corresponding number (as a
        string)"""

        self.logger.debug(
            'Entity: value: ' + ent['value'] + ' of type: ' + ent['entity'])
        etype = ent['entity']

        if etype == 'number':
            # TODO: Add error and type checking
            return ent['value']
        if etype == 'number-roman':
            # TODO: Add better error and type checking
            try:
                return str(roman.fromRoman(ent['value']))
            except:
                return None
        if etype == 'nth':
            # TODO: Add better error and type checking
            try:
                self.print_settings('converting using nthwords2int')
                return str(u.nthwords2int(ent['value'].lower()))
            except:
                return None
        if etype in ('nth-words', 'number-words'):
            # TODO: Add better error and type checking
            try:
                return str(u.text2int(ent['value'].lower()))
            except:
                return None

        # so we couldn't match the etype to convert
        return None

    def dict_factory(self, cursor, row):
        """Used for handling sqlite rows as dictionary (source: http://stackoverflow.com/questions/3300464/how-can-i-get-dict-from-sqlite-query)"""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d


    def greeting(self):
        """Outputs to the user the basic greeting at startup."""
        self.say_text('Hello! I\'m ' + self.botname + '.', greet=True)


    def before_quit(self):
        """Does any required closinng of resources prior to the programme quiting
        and then reports end of script execution"""
        try:
            self.cursor.close()
        except AttributeError, NameError:
            print('')
        try:
            self.db.close()
        except AttributeError, NameError:
            print('')
        try:
            self.logger.warn('Ending script execution now\n')
        except AttributeError, fNameError:
            print('Ending script execution now\n(logger was not found.)\n')
        sys.exit()


    def reset_last_ruler(self):
        """Resets the values relating to last ruler."""
        self.last_ruler_type = None
        self.last_ruler_id = None
        self.last_ruler_count = 0


    def handle_ctrl_c(self, signal, frame):
        # TODO: test the behaviour on Windows
        #       close down anything that should be closed before exiting
        self.before_quit()
        sys.exit(130)  # 130 is standard exit code for <ctrl> C


    def __init__(self, channels_out, channel_in = 'screen', loglvl = '', config_override = ''):
        """Initialises the core functionality and sets up various variables."""

        # TODO: add checks to confirm all necessary files are present and readable
        # (and writable if applicable)

        signal.signal(signal.SIGINT, self.handle_ctrl_c)

        self.logger = u.setup_custom_logger('root')

        if loglvl.lower().strip() == 'debug':
            self.logger.setLevel(logging.DEBUG)
            self.logger.info('Logging level set to DEBUG')
        elif loglvl.lower().strip() == 'info':
            self.logger.setLevel(logging.INFO)
            self.logger.info('Logging level set to INFO')
        elif loglvl.lower().strip() == 'warn':
            self.logger.setLevel(logging.WARN)
            self.logger.warn('Logging level set to WARN')
        elif loglvl.lower().strip() == '':
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.warn('Unrecognised log level input. Defaulting to WARN.')
        
        self.logger.info('Initialisation started')

        config = ConfigParser.SafeConfigParser()
        
        if config_override.strip() != '':
            config_file = os.path.abspath(config_override.strip())
        else:
            config_file = os.path.abspath(os.path.join('config', 'config_roybot.ini'))
        
        try:
            dataset = config.read([config_file])
            if len(dataset) == 0:
                raise IOError

        except IOError as e:
            self.logger.warn('Unable to open config file: ' + str(config_file))
            self.before_quit()
        except ConfigParser.Error as e:
            self.logger.warn('Error with config file: ' + str(config_file))
            self.before_quit()

        try:
            # bot items
            self.botname= config.get('bot', 'name')
            self.botsubject = config.get('bot', 'subject')
            # file items
            self.metadata_file = os.path.abspath(config.get('files', 'metadata_file'))
            self.sqlite_file = os.path.abspath(config.get('files', 'sqlite_file'))
            self.history_file = os.path.abspath(config.get('files', 'history_file'))
            self.demo_file = os.path.abspath(config.get('files', 'demo_file'))
            self.tagged_output_file = os.path.abspath(config.get('files', 'tagged_output_file'))
            self.email_output_file = os.path.abspath(config.get('files', 'email_output_file'))
        except ConfigParser.Error as e:
            self.logger.warn('Error reading configuration ' + str(e))

    # ---------------------------------------------
    # CUSTOMISE THESE ITEMS TO THIS PARTICULAR BOT
    # ---------------------------------------------

    # LC_AUTH_TOKEN eg yOGSQwMDEyYNg2YThiZ8GNh9MmF524hNDvZWM3OTMDIhOmZjOT
    #                  NlZGFhMmUzMDQxODM4M2MTU1ZjU3VmZjViYTAwY2Q5ZWNhYg==
    # LC_AUTH_TOKEN = 'XXXXX'
    # LC_USER_FILTER eg 386a8520a0328d0092baa475
    # LC_USER_FILTER = ['XXXXX']
    # LC_BASE_URL = 'http://localhost:8080/rooms/roybot'
    # LC_POLLING_TIME = 1

    # -----------------------
    # END OF CUSTOMISED ITEMS
    # -----------------------

        self.CHANNEL_IN = channel_in
        self.CHANNELS_OUT = channels_out

        self.msg_output = ''

        self.metadata = json.loads(open(self.metadata_file).read())
        self.interpreter = MITIEInterpreter(**self.metadata)
        self.db = sqlite3.connect(self.sqlite_file)
        self.db.row_factory = self.dict_factory
        self.cursor = self.db.cursor()
        self.rude_count = 0
        self.last_input = {}
        self.last_user_input = None
        self.email_text = ''
        self.email_subject = ''
        self.email_list = []
        self.reset_last_ruler()

        self.logger.info('Initialisation complete')


    def main_loop(self):
        """The main loop which repeats continuously until the programme is aborted
        or a crash occurs. It cycles round seeking input from which ever of the
        particular input modes the bot is configured to handle.
        It also handles low-level commands prior to passing input to Rasa NLU, such
        as toggling 'show parse' (s), tagging output (t), toggling verbose output (v),
        changing logging level (d=DEBUG, i=INFO , w=WARN) or quiting (q)"""
        self.show_parse = False
        self.verbose = True
        if os.path.exists(self.history_file):
            readline.read_history_file(self.history_file)
        self.prompt_text = u.STY_CURSOR + ' > ' + u.STY_USER
        try:
            while True:
                # if self.CHANNEL_IN == 'online':
                #     self.user_input = poll_LC()
                # elif self.CHANNEL_IN == 'email':
                #     self.email_item = poll_email()
                #     if self.email_item is None:
                #         self.user_input = ''
                #     else:
                #         self.user_input = self.email_item['user_input']
                # else:  # screen
                #     self.user_input = raw_input(self.prompt_text)
                self.user_input = raw_input(self.prompt_text) # when above section is uncommented then remove this line
                print(style.RESET, end="")
                if self.user_input.lower() == 'q':
                    print(
                        '\t\t' + u.STY_RESP + '  Okay.  Goodbye!  ' + u.STY_USER +
                        '\n')
                    self.before_quit()
                elif self.user_input.lower() == 't':
                    self.tag_last()
                elif self.user_input.lower() == 'v':
                    self.verbose = not self.verbose
                    self.print_settings('Verbose responses: ' + str(self.verbose))
                elif self.user_input.lower() == 's':
                    self.show_parse = not self.show_parse
                    self.print_settings(
                        'Show_parse: ' + {True: 'on', False: 'off'}[self.show_parse])
                elif self.user_input.lower() == 'c':
                    u.clear_screen()
                elif self.user_input.lower() == 'd':
                    self.logger.setLevel(logging.DEBUG)
                    self.logger.info('Logging level set to DEBUG')
                elif self.user_input.lower() == 'i':
                    self.logger.setLevel(logging.INFO)
                    self.logger.info('Logging level set to INFO')
                elif self.user_input.lower() == 'w':
                    self.logger.setLevel(logging.WARNING)
                    self.logger.warn('Logging level set to WARN')
                else:
                    self.check_input(self.user_input, self.show_parse, self.verbose)
                # if self.CHANNELS_OUT['email']:
                #     if self.email_item is not None:
                #         send_email(self.email_item['sender'])
        finally:
            readline.write_history_file(self.history_file)

    def print_settings(self, text, out=sys.stdout):
        """A screen only output function for printing settings changes that do not
        go to remote users. Typically to give a more human friendly and detailed
        level than might be sent to the logs."""
        print(u.STY_DESC + text + u.STY_USER)


    def say_text(self, text, greet=False, out=sys.stdout):
        """Handles 'saying' the output, with different approaches depending on the
        active channel (or channels) for output"""

        # Useful for unit tests
        sys.stdout = out

        if self.CHANNELS_OUT['facebook']:
            #must keep it under 600
            self.msg_output = (self.msg_output + '\n' + text)[:600]
            self.logger.debug('FB msg output: ' + self.msg_output)


        if self.CHANNELS_OUT['screen']:
            #text = text.decode('utf-8')
            if (len(text) > 0) and (text[0] == '>'):
                print(
                    '\n\t\t' + u.STY_CURSOR + ' > ' + u.STY_USER + text[1:],
                    end='  ' + u.STY_USER)
            else:
                print(
                    '\n\t\t' + u.STY_RESP + '  ' + text,
                    end='  ' + u.STY_USER + '\n\n')

        if self.CHANNELS_OUT['online']:
            self.LC_URL = self.LC_BASE_URL + '/messages'
            # We split on returns so that the entries get a new line (it's treated
            # as "code" entries otherwise :-( )
            for line in text.split('\n'):
                r = requests.post(
                    self.LC_URL, auth=(self.LC_AUTH_TOKEN, 'xxx'), data={'text': line})

        # if self.CHANNELS_OUT['email']:
        #     if self.greet is False:
        #         global email_text
        #         global email_subject
        #         if text[0] == '>':
        #             self.email_subject = self.botname + ' replying to your question - ' + \
        #                 text[1:].split('\n')[0]
        #             self.email_text = self.email_text + '> ' + text[1:].split('\n')[0] + '\n'
        #         else:
        #             self.email_text = self.email_text + text + '\n'

    def handle_greet(self, resp):
        """Handles the common intent of saying hello to a chatbot"""

        self.greeting()
        self.say_text('I\'m here to answer questions regarding ' + self.botsubject)
        if not(self.CHANNELS_OUT['facebook']):
            self.say_text('If you are stuck, you can ask for help or to see a demo')
        else:
            self.say_text('If you are stuck, you can ask for help or for an example question')

    def handle_origin(self, resp):
        """Handles intents relating to the origin of the bot, as this is often a
        question asked"""

        # -------------------------------------------------------------------------
        # CUSTOMISE THIS TO THE RASA NLU MODEL AND THE PURPOSE OF THIS BOT
        # -------------------------------------------------------------------------
        #
        # Entirely up to you, but this seems to be a common question people ask
        # of bots
        #
        # -------------------------------------------------------------------------

        self.say_text(
            'I am ' + self.botname + ', a simple chatbot focused on basic ' +
            'questions regarding ' + self.botsubject + '.\nI have been programmed ' +
            'in Python, using a machine learning backend that recognises user ' +
            'input and passes details to a script which in turn translates them ' +
            'so that relevant details can be accessed in a database, following ' +
            'which answers are constructed and given back to the user.')


    def handle_example(self, resp):
        """Handles giving a list of examples of valid input"""

        # -------------------------------------------------------------------------
        # CUSTOMISE THIS TO THE RASA NLU MODEL AND THE PURPOSE OF THIS BOT
        # -------------------------------------------------------------------------
        #
        # Entirely up to you, but the examples should have some variety and it may
        # be helpful to include some less "discoverable" ones
        #
        # -------------------------------------------------------------------------

        example_list = [
            'In the House of Anjou who was the last ruler?',
            'Tell me all about Henry VIII',
            'Who was king after Richard the Lionheart?',
            'What date was Elizabeth I born?',
            'What were the circumstances of Edward II\'s death?',
            'What can I say?'
            ]

        suggestion_intro = random.choice([
            'Here\'s an example to try:\n\t',
            'How about this?\n\t',
            'Give this a go!\n\t'])

        self.say_text(suggestion_intro + ' "' + random.choice(example_list) + '"?')


    def handle_deflect(self, resp):
        """Handles deflecting the user if the intent is perhaps understood but
        not core to the bot function"""

        # -------------------------------------------------------------------------
        # CUSTOMISE THIS TO THE RASA NLU MODEL AND THE PURPOSE OF THIS BOT
        # -------------------------------------------------------------------------

        comment_list = [
            'I can\'t really respond to that sort of thing.',
            'That isn\'t something I\'m programmed to handle.',
            'Sorry, I cannot help you on that line of discussion.',
            'No comment.',
            'Sorry, I don\'t know about that.'
            ]

        # NB: although this is somewhat generic, it is worth customising this more
        # specifically to the bot subject so the language sounds more natural than
        # it does with the substituted botsubject alone (otherwise people *will*
        # notice it is clunky!)
        suggestion_list = [
            'How about asking me something about ' + self.botsubject + '?',
            'Let\'s stick to questions about ' + self.botsubject + '.',
            'We\'ll get further if we stick to ' + self.botsubject +
            ' related questions.', 'My knowledge only really extends to matters' +
            ' related to ' + self.botsubject + '.'
            ]

        self.say_text(
            random.choice(comment_list) + '\n\n' + random.choice(suggestion_list))


    def handle_rude(self, resp):
        """Handles rude input. An inevitable and unfortunate case, but it is bound
        to come up!"""

        # -------------------------------------------------------------------------
        # CUSTOMISE THIS TO THE RASA NLU MODEL AND THE PURPOSE OF THIS BOT
        # -------------------------------------------------------------------------
        #
        # In some scenarios it is best to ignore this input and the responses will
        # vary depending on whether the bot is casual, playful, cheeky itself, or
        # more formal, serious and business like.
        #
        # Pay attention to the training too and possibly temper the responses if
        # you are likely to get false-positives! It isn't great to accuse a user of
        # being rude when it is merely the intent recognition that is failing with
        # a perfectly reasonable user input!
        #
        # -------------------------------------------------------------------------

        replies_initial = [
            'That isn\'t something I can really comment on.',
            'Perhaps I\'ve misunderstood what you meant to say?',
            'Is there anything useful I can help you with?',
            'I\'m not sure I understood what you just said.',
            'Ah the rich expressive nature of the English language. ' +
            'Sadly I\'m just a simple bot so it means very little to me!'
            ]
        replies_more_direct = [
            'There\'s no need for rudeness, I\'m not going to rise to it!',
            'I\'m sensing some anger or rudeness here, but sadly I don\'t have ' +
            'the skills to respond appropriately.',
            'Sounds like a word from my naughty list!',
            'Look, if you want to take things out on someone why not try the ' +
            'internet!?',
            'I am not programmed to handle rudeness in any meaningful way. We ' +
            'can do this all day if you like!']

        self.rude_count += 1

        if self.rude_count < 3:
            self.say_text(random.choice(replies_initial))
        else:
            self.say_text(random.choice(replies_more_direct))
            if self.rude_count > 5:
                self.rude_count = 0


    def handle_help(self, resp):
        # -------------------------------------------------------------------------
        # CUSTOMISE THIS TO THE PURPOSE OF THIS BOT
        # -------------------------------------------------------------------------
        #
        # How this is phrased will vary depending on whether the bot is casual,
        # cheeky, or more formal and serious.
        #
        # It will depend on the usage, but it may be preferable to skip details
        # that suggests the underlying storage in much detail (ie not to mention
        # rows and fields directly)
        #
        # -------------------------------------------------------------------------

        replies_initial = [
            'I understand a handful of simple concepts related to ' + self.botsubject +
            '.\n\nThere are various ways to select a particular ruler, such as ' +
            'the number (eg VI, 6 or sixth) or by a value (eg "William Rufus").\n\n' +
            'Then you can pick out specific information such as:\n - Date of birth\n' +
            ' - End of reign\n - Famous battles\n - House (eg of Tudor)\n\nThen the ML magic happens, ' +
            'I try to understand what you\'ve said and then look up details ' +
            'based on entities recognised in a database.\n\nHave a go!\n\n' +
            '(or try "Example" if you\'re really not sure']
        self.say_text(random.choice(replies_initial))


    def handle_demo(self, resp, show_parse, verbose):
        """Handles output of a series of demo inputs (automatically submitted in
        sequence) along with their responses. The inputs are read from a demo text
        file (one per line). To be effective the model must be trained for the
        inputs."""

        # -------------------------------------------------------------------------
        # CUSTOMISE demo_file CONTENTS TO THE PURPOSE OF THIS BOT (NO CHANGES
        # REQUIRED IN THE CODE HERE)
        # -------------------------------------------------------------------------

        demo_delay = 1
        self.print_settings('Running automated demo')
        for ent in resp['entities']:
            if ent['entity'].lower() == 'speed':
                if ent['value'].lower() in ['quick', 'fast']:
                    demo_delay = 0
        prompt_text = '>'
        try:
            with open(self.demo_file, 'r') as f:
                for line in f:
                    self.say_text(prompt_text + line)
                    time.sleep(demo_delay)
                    self.check_input(line, show_parse, verbose)
                    time.sleep(demo_delay)

            self.print_settings('Automated demo complete')
        except IOError as e:
            self.logger.warn('Unable to open demo file: ' + str(self.demo_file)) #Does not exist OR no read permissions


    def is_multi_item_field(self, field):
        """True if the field is one where the database contains multiple items in a single field (eg as for
        FamousBattles, where there can be zero to many battles)"""
        if field in ('FamousBattles'):
            return True


    def determine_result_cardinality(self, text, splitter):
        """Takes input text and determines cardinality of items referenced, returning 1 (for singular) or 2 (for plural)"""
        if text is not None:
            return min(2, len(text.split(splitter)))
        else:
            return 1


    def resolve_gender_text(self, template_text, ruler_type):
        """Switches the appropriate gendered words into the sentence"""
        self.logger.debug('resolve_gender_text: ruler_type: ' + ruler_type)
        if ruler_type == 'king':
            sub_dict = {'HeShe':'He', 'hisher':'his'}
        if ruler_type == 'queen':
            sub_dict = {'HeShe':'She', 'hisher':'her'}

        t = Template(template_text)
        return t.safe_substitute(**sub_dict)


    def match_template(self, resp, fields, params, plural_singlar = ''):

        matching_templates = []

        template_intent = resp['intent']
        # Mappings for any intents where the handle function is "re-used" but we
        # want to reduce number of templates needed and can use them in both cases
        if template_intent == 'ruler_pronoun_feature':
            template_intent = 'ruler_feature' 

        self.logger.debug('Template intent for match_template is: ' + template_intent)

        templates = [
            {
                'intent': 'ruler_list',
                'template_text': '$Name $Number'},
            {
                'intent': 'ruler_before',
                'template_text': '$Name $Number'},
            {
                'intent': 'ruler_after',
                'template_text': '$Name $Number'},
            {
                'intent': 'ruler_feature',
                'template_text': '$HeShe reigned from $ReignStartDt'},
            {
                'intent': 'ruler_feature',
                'template_text': '$HeShe reigned until $ReignEndDt'},
            {
                'intent': 'ruler_feature',
                'template_text': '$NotableEventsDuringLife'},
            {
                'intent': 'ruler_feature',
                'template_text': '$HeShe was born on $DtBirth'},
            {
                'intent': 'ruler_feature',
                'template_text': '$HeShe died on $DtDeath'},
            {
                'intent': 'ruler_feature',
                'template_text': '$Portrait'},
            {
                'intent': 'ruler_feature',
                'template_text': '$DeathCircumstances'},
            {
                'intent': 'ruler_feature',
                'template_text': '$FamousBattles',
                'template_text_singular': 'An important battle was the $FamousBattles',
                'template_text_plural': 'Some important battles were: $FamousBattles'},
            {
                'intent': 'ruler_feature',
                'template_text': '$Description'},
            {
                'intent': 'ruler_feature',
                'template_text': '$Name $Number was born on $DtBirth and died on $DtDeath.\nWith a reign starting in $ReignStartDt and lasting until $ReignEndDt $HeShe was involved in $FamousBattles\n$Description'}
            ]

        max_field_count = 0
        for t in templates:
            t_field_count = 0
            if t['intent'] == template_intent:
                for f in fields:
                    if f in t['template_text']:
                        t_field_count = t_field_count + 1
                if t_field_count == max_field_count:
                    matching_templates.append(t)             
                if t_field_count > max_field_count:
                    matching_templates = []
                    matching_templates.append(t)
                    max_field_count = t_field_count

        self.logger.debug('max_field_count is: ' + str(max_field_count))

        # TODO: put in a better 'fitness' selection process here!!
        if max_field_count != 0:
            if matching_templates != []:
                self.logger.debug('Count of possible matching_templates is: ' + str(len(matching_templates)))
                # Until there are equivalent meaning templates (which score equally) best not
                # to have a random choice made
                # chosen_template = random.choice(matching_templates)            
                chosen_template = matching_templates[0]
            else:
                # Default template
                self.logger.debug('matching_templates list is empty, so switch answer text to cannot answer')
                chosen_template = {
                    'intent': 'unmatched',
                    'template_text': 'Sorry I cannot answer that.'} 
        else:
            # Default template
            self.logger.debug('max_field_count == 0, so switch answer text to cannot answer')
            chosen_template = {
                'intent': 'unmatched',
                'template_text': 'Sorry I cannot answer that.'} 
        # TODO: put in the option to do substitution here (most likely scenario,
        #      barring edge cases)
        if (plural_singlar == 'singular') & ('template_text_singular' in chosen_template):
            return chosen_template['template_text_singular']
        if (plural_singlar == 'plural') & ('template_text_plural' in chosen_template):
            return chosen_template['template_text_plural']
        return chosen_template['template_text']

    def handle_ruler_before_after(self,
                            resp,
                            detail=False,
                            verbose=False,
                            before=True):
        """Handles the intent seeking the ruler before another specified ruler."""

        self.logger.info('Intent: ruler_before')

        ## Before
        # SELECT *
        # FROM ruler
        # WHERE RulerId < (SELECT RulerId FROM ruler WHERE Name = 'Henry' AND `Number` = '8')
        # ORDER BY RulerId DESC
        # LIMIT 1

        ## After
        # SELECT *
        # FROM ruler
        # WHERE RulerId > (SELECT RulerId FROM ruler WHERE Name = 'Henry' AND `Number` = '8')
        # ORDER BY RulerId
        # LIMIT 1

        sql = "SELECT `Name`, `Number`, `RulerId`, `RulerType` FROM ruler WHERE RulerId "
        sql_middle = " (SELECT RulerId FROM ruler"
        
        if before:
            sql = sql + '<' + sql_middle
            sql_suffix = "ORDER BY RulerId DESC LIMIT 1"
        else:
            # after
            sql = sql + '>' + sql_middle
            sql_suffix = "ORDER BY RulerId LIMIT 1"

        fields = ['Name', 'Number']

        num = None
        loc = None
        ruler_type = None

        where = []
        sub_where = []
        params = {}
        for ent in resp['entities']:
            if ent['entity'].lower() in (
                    'name', 'location', 'number', 'number-words',
                    'number-roman', 'nth-words', 'nth', 'title','ruler_type'):
                self.logger.debug(
                    'Selection entity found: ' + ent['value'] +
                    ' (' + ent['entity'] + ')')
                if ent['entity'].lower() == 'ruler_type':
                    ruler_type = ent['value'].lower()
                    # TODO: consider breaking out this mapping into a generalised helper function
                    if ruler_type in ('king', 'kings', 'men', 'males'):
                        ruler_type = 'king'
                    if ruler_type in ('queen', 'queens', 'women', 'females'):
                        ruler_type = 'queen'
                    if ruler_type not in ('monarch', 'ruler'):  # or any other non-restricting ruler_types
                        where.append('RulerType = :RulerType')
                        params['RulerType'] = ruler_type
                if ent['entity'].lower() == 'name':
                    name = ent['value']
                    sub_where.append('Name = :Name')
                    params['Name'] = name
                if ent['entity'].lower() == 'title':
                    title = ent['value']
                    sub_where.append('Title = :Title')
                    params['Title'] = title
                if ent['entity'].lower() == 'location':
                    loc = ent['value']
                    sub_where.append('Country LIKE :Location')
                    params['Location'] = '%' + loc + '%'
                if ent['entity'].lower() in (
                        'number', 'number-roman', 'nth',
                        'nth-words', 'number-words'):
                    num = self.map_entity_to_number(ent)
                    if num is not None:
                        sub_where.append('Number = :Number')
                        params['Number'] = num

        if loc is not None:
            self.logger.debug('Loc: ' + str(loc))
        if num is not None:
            self.logger.debug('Num: ' + str(num))
        if where:
            sql_suffix = ") AND {} ".format(' AND '.join(where)) + sql_suffix
        else:
            sql_suffix = ") " + sql_suffix
        if sub_where:
            sql = '{} WHERE {}'.format(sql, ' AND '.join(sub_where))
            sql = sql + sql_suffix
        self.logger.info('SQL: ' + sql)
        self.logger.info('Params: ' + str(params))
        try:
            self.cursor.execute(sql, params)
        except sqlite3.Error as e:
            self.say_text('I experienced a problem answering that question. Could we try another question instead?')
            return
        output = ''
        results = self.cursor.fetchall()
        self.last_ruler_count = len(results)
        self.logger.debug('Last ruler count: ' + str(self.last_ruler_count))
        if self.last_ruler_count == 1:
            self.last_ruler_type = results[0]['RulerType']
            self.logger.debug('Set last_ruler_type to: ' + str(self.last_ruler_type))
            self.last_ruler_id = results[0]['RulerId']
            self.logger.debug('Set last_ruler_id to: ' + str(self.last_ruler_id))
        else:
            if self.last_ruler_count == 0:
                self.say_text('Based on my understanding of your question, I am not able to match any rulers. You may have a typo or a non-existent combination (eg Richard VII).')
            else:
                self.say_text('Based on my understanding of your question, I\'m having trouble narrowing down the selection to a single ruler. You may need to be a little more specific.')
            self.reset_last_ruler()
            return

        if verbose is True:
            template_text = self.match_template(resp, fields, params)
            #say_text(template_text)

        for row in results:
            row = self.format_row(row)
            self.logger.info(row)
            output = self.merge_output(row)
            if verbose is True:
                # if moving to Python 3.2+ then could possibly use this:
                # template_row = defaultdict(lambda: '<unset>', **row)
                # self.say_text(template.format(**template_row))
                # instead use this which doesn't default missing values:
                t = Template(template_text)
                template_output = str(t.safe_substitute(**row))
                if 'None' in template_output or len(template_output.strip()) == 0:
                    template_output = 'Sorry the information to answer that question is missing.'
                self.say_text(template_output)
                # alt way of doing this: self.say_text(string.Formatter().vformat(template, (), defaultdict(str, **row)))
            else:
                self.say_text(output)


    def handle_ruler_list(self,
                            resp,
                            detail=False,
                            verbose=False):
        """Handles the intent where a question seeks a list of rulers in a particular group or potentially the first or last of such a group."""

        self.logger.info('Intent: ruler_list')
        # Core query: SELECT * FROM `ruler` WHERE xyz... ORDER BY date(ReignStartDt)
        # If all or first or last variant, must add:
        #   All:    ASC
        #   First:  ASC LIMIT 1
        #   Last:   DESC LIMIT 1
        
        # additional cases: if they list a year, then find ruler(s) in that year
        # SELECT * FROM ruler WHERE CAST(STRFTIME('%Y', ReignStartDt) AS INT) <= 1400 AND CAST(STRFTIME('%Y', ReignEndDt) AS INT) >= 1400
        sql = 'SELECT `Name`, `Number`, `RulerId`, `RulerType` FROM `ruler`'
        fields = ['Name', 'Number']
        country = None
        house = None
        position = None
        year = None
        century_start = None
        century_end = None
        ruler_type = None
        where = []
        params = {}
        sql_suffix = ' ORDER BY date(ReignStartDt)'

        for ent in resp['entities']:
            if ent['entity'].lower() in (
                    'ruler_type', 'country', 'location', 'house', 'year', 'period', 'position'):
                self.logger.debug(
                    'Selection entity found: ' + ent['value'] +
                    ' (' + ent['entity'] + ')')
                if ent['entity'].lower() == 'ruler_type':
                    ruler_type = ent['value'].lower()
                    # TODO: consider breaking out this mapping into a generalised helper function
                    if ruler_type in ('king', 'kings', 'men', 'males'):
                        ruler_type = 'king'
                    if ruler_type in ('queen', 'queens', 'women', 'females'):
                        ruler_type = 'queen'
                    if ruler_type not in ('monarch', 'ruler'):  # or any other non-restricting ruler_types
                        where.append('RulerType = :RulerType')
                        params['RulerType'] = ruler_type
                if ent['entity'].lower() in ('country', 'location'):
                    # TODO: add ability to handle selection by one of a ruler's countries
                    #   (eg select by England only if ruler rules England and Scotland)
                    country = ent['value']
                    where.append('Country LIKE :Country')
                    params['Country'] = '%' + country + '%'

                if ent['entity'].lower() == 'house':
                    # TODO: make selection less brittle
                    house = ent['value']
                    where.append('House = :House')
                    params['House'] = house
                
                if ent['entity'].lower() == 'year':
                    year = ent['value']
                    where.append("CAST(STRFTIME('%Y', ReignStartDt) AS INT) <= :Year AND CAST(STRFTIME('%Y', ReignEndDt) AS INT) >= :Year")
                    params['Year'] = year

                if ent['entity'].lower() == 'period':
                    if ent['value'].lower() == 'century':
                        for n in resp['entities']:
                            if n['entity'].lower() in (
                                    'number', 'number-roman', 'nth',
                                    'nth-words', 'number-words'):
                                num = self.map_entity_to_number(n)
                                if num is not None:
                                    century_end = int(num) * 100
                                    century_start = century_end - 100
                                    where.append("CAST(STRFTIME('%Y', ReignStartDt) AS INT) <= :CenturyEnd AND CAST(STRFTIME('%Y', ReignEndDt) AS INT) >= :CenturyStart")
                                    params['CenturyEnd'] = century_end
                                    params['CenturyStart'] = century_start

                if ent['entity'].lower() == 'position':
                    position = ent['value'].lower()
                    # TODO: expand this to cope with second, third etc of
                    if position in ('first', 'earliest', 'start', 'beginning'):
                        sql_suffix = sql_suffix + ' ASC LIMIT 1'
                    if position in ('last', 'latest', 'final', 'end'):
                        sql_suffix = sql_suffix + ' DESC LIMIT 1'
        if ruler_type is not None:
            self.logger.debug('Ruler Type: ' + str(ruler_type))
        if country is not None:
            self.logger.debug('Country: ' + str(country))
        if house is not None:
            self.logger.debug('House: ' + str(house))
        if position is not None:
            self.logger.debug('Position: ' + str(position))
        else:
            sql_suffix = sql_suffix + ' ASC'
        if where:
            sql = '{} WHERE {}'.format(sql, ' AND '.join(where))
            sql = sql + sql_suffix
        self.logger.info('SQL: ' + sql)
        self.logger.info('Params: ' + str(params))
        try:
            self.cursor.execute(sql, params)
        except sqlite3.Error as e:
            self.say_text('I experienced a problem answering that question. Could we try another question instead?')
            return
        output = ''
        results = self.cursor.fetchall()
        self.last_ruler_count = len(results) 
        if self.last_ruler_count == 1:
            self.last_ruler_type = results[0]['RulerType']
            self.logger.debug('Set last_ruler_type to: ' + str(self.last_ruler_type))
            self.last_ruler_id = results[0]['RulerId']
            self.logger.debug('Set last_ruler_id to: ' + str(self.last_ruler_id))
        else:
            if self.last_ruler_count == 0:
                self.say_text('Based on my understanding of your question, I am not able to match any rulers. You may have a typo or a non-existent combination.')
            if (position is not None) and (self.last_ruler_count > 1):
                self.say_text('It looks like you were after a specific ruler, but I am matching several (so perhaps something went wrong, either with how the question was asked or how I understood it).')
                self.say_text('Here they are anyway:')
            self.reset_last_ruler()

        template_text = ''

        for row in results:
            row = self.format_row(row)
            self.logger.info(row)
            output = self.merge_output(row)
            if verbose is True:
                if template_text == '':
                    cardinalty = ''
                    for item in row:
                        if self.is_multi_item_field(item):
                            if self.determine_result_cardinality(row[item], ';') == 2:
                                cardinalty = 'plural'
                            else:
                                cardinalty = 'singular'
                    #template_text = self.match_template(resp, fields, params, cardinalty)
                    # hard-coding values for "fields" here as they're the only items we need to check and there
                    # is no actual fields list here 
                    template_text = self.match_template(resp, fields, params)
                    if self.last_ruler_type is not None:
                        #print('xx')
                        template_text = self.resolve_gender_text(template_text, self.last_ruler_type)
                # if moving to Python 3.2+ then could possibly use this:
                # template_row = defaultdict(lambda: '<unset>', **row)
                # self.say_text(template.format(**template_row))
                # instead use this which doesn't default missing values:
                t = Template(template_text)
                template_output = str(t.safe_substitute(**row))
                if 'None' in template_output or len(template_output.strip()) == 0:
                    template_output = 'Sorry the information to answer that question is missing.'
                self.say_text(template_output)
                # alt way of doing this: self.say_text(string.Formatter().vformat(template, (), defaultdict(str, **row)))
            else:
                self.say_text(output)


    def handle_ruler_pronoun_feature(self,
                               resp,
                               detail=False,
                               verbose=False):

        self.logger.info('Intent: ruler_pronoun_feature')
        self.logger.debug('last_ruler_id: ' + str(self.last_ruler_id))
        if self.last_ruler_id is not None:
            self.handle_ruler_feature(resp, detail, self.last_ruler_id, verbose)
        else:
            self.say_text('I am not sure which ruler you are referring to. Please restate your question directly mentioning them.')


    def handle_ruler_feature(self,
                               resp,
                               detail=False,
                               overload_item=None,
                               verbose=False):

        self.logger.info('Intent: ruler_feature')
        sql = 'SELECT DISTINCT {fields} FROM `ruler`'
        num = None
        loc = None
        fields = []
        where = []
        params = {}
        for ent in resp['entities']:
            if ent['entity'].lower() in (
                    'name', 'location', 'number', 'number-words',
                    'number-roman', 'nth-words', 'nth', 'title'):
                self.logger.debug(
                    'Selection entity found: ' + ent['value'] +
                    ' (' + ent['entity'] + ')')
                if ent['entity'].lower() == 'name':
                    name = ent['value']
                    where.append('Name = :Name')
                    params['Name'] = name
                if ent['entity'].lower() == 'title':
                    title = ent['value']
                    where.append('Title = :Title')
                    params['Title'] = title
                if ent['entity'].lower() == 'location':
                    loc = ent['value']
                    where.append('Country LIKE :Location')
                    params['Location'] = '%' + loc + '%'
                if ent['entity'].lower() in (
                        'number', 'number-roman', 'nth',
                        'nth-words', 'number-words'):
                    num = self.map_entity_to_number(ent)
                    if num is not None:
                        where.append('Number = :Number')
                        params['Number'] = num
            else:
                if not detail:
                    self.logger.info(
                        'A field related entity was found: ' +
                        ent['value'] + ' (' + ent['entity'] + ')')
                    f = self.map_feature_to_field(ent['value'])
                    #if (f is not None) & (f not in fields):
                    #    fields.append(f)
                    fields = fields + list(set(f) - set(fields)) # adds only those not already in list

        if overload_item is not None:
            where = ["RulerId = :RulerId"]
            params['RulerId'] = overload_item

        if 'RulerId' not in fields:
            fields.append('RulerId')
        if 'RulerType' not in fields:
            fields.append('RulerType')
        self.logger.debug('Fields: ' + str(fields))
        if overload_item is not None:
            self.logger.debug('Overload item: ' + str(overload_item))
        if loc is not None:
            self.logger.debug('Loc: ' + str(loc))
        if num is not None:
            self.logger.debug('Num: ' + str(num))
        if fields:
            sql = sql.format(fields=', '.join(fields))
        else:
            sql = sql.format(fields='*')
        if where:
            sql = '{} WHERE {}'.format(sql, ' AND '.join(where))
        self.logger.info('SQL: ' + sql)
        self.logger.info('Params: ' + str(params))
        try:
            self.cursor.execute(sql, params)
        except sqlite3.Error as e:
            self.say_text('I experienced a problem answering that question. Could we try another question instead?')
            return
        output = ''
        results = self.cursor.fetchall()
        self.last_ruler_count = len(results)
        self.logger.debug('Last ruler count: ' + str(self.last_ruler_count))
        if self.last_ruler_count == 1:
            self.last_ruler_type = results[0]['RulerType']
            self.logger.debug('Set last_ruler_type to: ' + str(self.last_ruler_type))
            self.last_ruler_id = results[0]['RulerId']
            self.logger.debug('Set last_ruler_id to: ' + str(self.last_ruler_id))
        else:
            if self.last_ruler_count == 0:
                self.say_text('Based on my understanding of your question, I am not able to match any rulers. You may have a typo or a non-existent combination (eg Richard VII).')
            else:
                self.say_text('Based on my understanding of your question, I cannot narrow down the selection to a single ruler. You may need to be a little more specific.')
            self.reset_last_ruler()
            return

        template_text = ''

        for row in results:
            row = self.format_row(row)
            self.logger.info(row)
            output = self.merge_output(row)
            if verbose is True:
                if template_text == '':
                    cardinalty = ''
                    for item in row:
                        if self.is_multi_item_field(item):
                            if self.determine_result_cardinality(row[item], ';') == 2:
                                cardinalty = 'plural'
                            else:
                                cardinalty = 'singular'
                    template_text = self.match_template(resp, fields, params, cardinalty)
                    if self.last_ruler_type is not None:
                        #print('xx')
                        template_text = self.resolve_gender_text(template_text, self.last_ruler_type)
                t = Template(template_text)
                template_output = str(t.safe_substitute(**row))
                if 'None' in template_output or len(template_output.strip()) == 0:
                    template_output = 'Sorry the information to answer that question is missing.'
                self.say_text(template_output)
                # alt way of doing this: self.say_text(string.Formatter().vformat(template, (), defaultdict(str, **row)))
            else:
                self.say_text(output)


    def merge_output(self, row):
        output = ''
        for f in row:
            try:
                output = output + str(row[f]) + ', '
            except UnicodeEncodeError:
                output = output + str(row[f].encode('utf-8')) + ', '
        # TODO: put something to take off the final comma
        return output

    def format_row(self, row):
        for item in row:
            if 'Dt' in str(item):
                if (row[item] is not None) & (row[item] != '') & (row[item] != 'Present'):
                    try:
                        row[item] = str(arrow.get(str(row[item]), 'YYYY-MM-DD').format('DD MMMM YYYY'))
                    except Exception as e:
                        self.logger.debug('Cannot convert contents of date field ' + str(item) + ' to a formatted date. ' + str(e))
            if item in ('Number'):
                row[item] = str(roman.toRoman(int(row[item])))
        return row

    def check_input(self, u_input, show_parse=False, verbose=False):
        """Checks the user supplied input and passes it to the Rasa NLU model to
        get the intent and entities"""
        self.logger.debug('User input: ' + u_input)
        u_input = u.clean_input(u_input)
        self.logger.debug('User input (cleaned): ' + u_input)
        if len(u_input) == 0:
            self.logger.debug('Skipping empty input')
            self.say_text('I\'m unsure what to say to that! :/')
            return
        resp = self.interpreter.parse(u_input)
        if show_parse:
            self.print_settings('\tParse output:\n\t\t' + str(resp))
        self.last_input = resp
        if 'intent' in resp:
            # ---------------------------------------------------------------------
            # THIS IS WHERE YOU UPDATE THE CUSTOM INTENTS THAT YOU HAVE TRAINED
            # RASA NLU TO HANDLE
            # ---------------------------------------------------------------------
            if resp['intent'] == 'ruler_feature':
                # the "handle_{intent name}" is merely a convention for
                # readibility; they could just as well be called any acceptable
                # function name (for Python) that you like but try to keep the
                # meaning clear if possible.
                self.handle_ruler_feature(resp, False, verbose=verbose)
            elif resp['intent'] == 'detail_example':
                # in some scenarios it might be useful to re-use the same intent
                # handling but passing a distinct parameter
                self.handle_ruler_feature(resp, True)
            elif resp['intent'] == 'ruler_pronoun_feature':
                self.handle_ruler_pronoun_feature(resp, False, verbose=verbose)
            elif resp['intent'] == 'ruler_list':
                self.handle_ruler_list(resp, False, verbose=verbose)
            elif resp['intent'] == 'ruler_after':
                self.handle_ruler_before_after(resp, False, verbose=verbose, before=False)
            elif resp['intent'] == 'ruler_before':
                self.handle_ruler_before_after(resp, False, verbose=verbose, before=True)
            elif resp['intent'] == 'rude':
                self.handle_rude(resp)
            elif resp['intent'] == 'deflect':
                self.handle_deflect(resp)
            elif resp['intent'] == 'help':
                self.handle_help(resp)
            elif resp['intent'] == 'example':
                self.handle_example(resp)
            elif resp['intent'] == 'origin':
                self.handle_origin(resp)
            elif resp['intent'] == 'greet':
                self.handle_greet(resp)
            elif resp['intent'] == 'demo':
                if not(self.CHANNELS_OUT['facebook']):
                    self.handle_demo(resp, show_parse, verbose=verbose)
                else:
                    self.handle_example(resp)
            else:
                self.say_text(
                    'I believe I understood what you meant (' + resp['intent'] + ') but I do ' +
                    'not have the necessary skills to respond appropriately. ' +
                    'Sorry!')
        else:
            self.logger.info('Sorry, but I cannot understand your question.')


    def tag_last(self):
        """Ouputs tagged items (ie responses of some particular interest, typically
        due to an error) to a file"""
        self.print_settings('Tagged: ' + str(self.last_input))
        try:
            with open(self.tagged_output_file, "a") as f:
                f.write(str(self.last_input) + '\n')
        except IOError as e:
            self.logger.warn('Unable to open tagged output file: ' + str(self.tagged_output_file)) #Does not exist OR no read permissions

# class LetsChat:
#     """For interactions with Let's Chat"""
#
#     def poll_LC():
#         """Polls the Let's Chat room associated with the bot for any new
#         messages"""
#         LC_URL = LC_BASE_URL + '/messages?take=1'
#         user_input = ''
#         global last_user_input
#         while True:
#             time.sleep(LC_POLLING_TIME)
#             try:
#                 r = requests.get(LC_URL, auth=(LC_AUTH_TOKEN, 'xxx'))
#                 self.logger.debug(r.text)
#                 if r.json()[0]['owner'] in LC_USER_FILTER:
#                     self.logger.debug('Owner matches: ' + str(r.json()[0]['owner']))
#                     user_input = r.json()[0]['text']
#                     if (user_input[0:4] != 'http') & \
#                             (user_input != last_user_input):
#                         if last_user_input:
#                             last_user_input = user_input
#                             self.logger.debug('We have a new input')
#                             self.logger.debug('user_input is: ' + user_input)
#                             break
#                         else:
#                             last_user_input = user_input
#             except:
#                 self.logger.warn('Error in poll_LC' + str(sys.exc_info()[0]))
#         self.logger.debug('Returning  user_input: ' + user_input)
#         return user_input


# def poll_email():
#     """Polls the list of unprocessed emails and if there aren't any it will
#     check the email account directly"""
#     global email_list
#     # TODO: look into better performance versions of this (pop(0) isn't great
#     #      apparently)
#     if len(email_list) > 0:
#         prompt_text = '>'
#         email_item = email_list.pop(0)
#         self.say_text(prompt_text + email_item['user_input'] + '\n')
#         return email_item
#     else:
#         time.sleep(30)
#         email_list.extend(download_emails())
#         return None

@click.command()
@click.option('--config', default='', help='The location of the config file.')
@click.option('--loglvl', default='', help='The level at which logging is done (DEBUG / INFO / WARN). Not case sensitive. Default level is WARN.')
def main(config, loglvl):
    """RoyBot: a simple chatbot programme to look up details about the rulers of England"""
    ch_in = 'screen'  # 'email' OR 'screen' OR 'online'
    ch_out = {'facebook': False, 'email': False, 'online': False, 'screen': True} # 'facebook': True
    c = Core(channels_out = ch_out, channel_in = ch_in, loglvl = loglvl, config_override = config)
    c.greeting()
    c.main_loop()


if __name__ == '__main__':
    main()
