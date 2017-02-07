from __future__ import print_function
import sys
import signal
import os
import random
import time
import readline
import logging
from colored import fore, back, style
import json
import sqlite3
import requests
import roman
from rasa_nlu.interpreters.mitie_interpreter import MITIEInterpreter
import imaplib
import smtplib
import email
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import ConfigParser
import re

# ---------------------------------------------
# CUSTOMISE THESE ITEMS TO THIS PARTICULAR BOT
# ---------------------------------------------

BOTNAME = 'RoyBot'
BOTSUBJECT = ' royalty in England (to begin with, Scotland to come later on!)'
METADATA_LOCATION = os.path.abspath(os.path.join(
    'models','model_20170206-042538', 'metadata.json'))
SQLITE_FILE = os.path.abspath(os.path.join('data', 'roybot_db.sqlite'))
HISTORY_FILENAME = os.path.abspath(os.path.join('data', 'roybot.hist'))
DEMO_FILE = os.path.abspath(os.path.join('data', 'roybot_demo_inputs.txt'))

# LC_AUTH_TOKEN eg yOGSQwMDEyYNg2YThiZ8GNh9MmF524hNDvZWM3OTMDIhOmZjOT
#                  NlZGFhMmUzMDQxODM4M2MTU1ZjU3VmZjViYTAwY2Q5ZWNhYg==
LC_AUTH_TOKEN = 'XXXXX'
# LC_USER_FILTER eg 386a8520a0328d0092baa475
LC_USER_FILTER = ['XXXXX']
LC_BASE_URL = 'http://localhost:8080/rooms/roybot'
LC_POLLING_TIME = 1

TAGGED_OUTPUT_FILE = os.path.abspath(os.path.join('data', 'roybot_tagged.txt'))
EMAIL_OUTPUT_FILE = os.path.abspath(os.path.join('data', 'roybot_email.txt'))

# -----------------------
# END OF CUSTOMISED ITEMS
# -----------------------

CHANNEL_IN = 'screen'  # 'email' OR 'screen' OR 'online'
CHANNELS_OUT = {'email': False, 'online': False, 'screen': True}

STY_DESC = fore.LIGHT_GREEN + back.BLACK
STY_DESC_DEBUG = fore.SKY_BLUE_1 + back.BLACK + style.DIM
STY_HELP = fore.DARK_SLATE_GRAY_3 + back.BLACK
STY_HIDDEN = fore.BLACK + back.BLACK
STY_USER = style.RESET + fore.WHITE + back.BLACK
STY_CURSOR = fore.LIGHT_GOLDENROD_2B + back.BLACK + style.BOLD
STY_RESP = fore.WHITE + back.MEDIUM_VIOLET_RED + style.BOLD
# STY_RESP = fore.WHITE + back.GREY_11 + style.BOLD #+ style.NORMAL
STY_EMAIL = fore.WHITE + back.GREY_11 + style.BOLD
STY_RESP_SPECIAL = fore.WHITE + back.LIGHT_GOLDENROD_2B + style.BOLD
STY_HIGHLIGHT = fore.DEEP_PINK_4C + back.BLACK
STY_DRAW = fore.WHITE + back.BLACK + style.BOLD

logger = logging.getLogger(BOTNAME)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.WARN)
# ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    STY_DESC_DEBUG + '%(asctime)s - %(name)s - %(levelname)8s - %(message)s' +
    style.RESET, datefmt='%Y-%b-%d %H:%M:%S')
ch.setFormatter(formatter)
logger.addHandler(ch)

numwords = {}


def handle_ctrl_c(signal, frame):
    # TODO: test the behaviour on Windows
    #       close down anything that should be closed before exiting
    before_quit()
    sys.exit(130)  # 130 is standard exit code for <ctrl> C


def nthwords2int(nthword):
    """Takes an "nth-word" (eg 3rd, 21st, 28th) strips off the ordinal ending
    and returns the pure number."""

    ordinal_ending_chars = 'stndrh'  # from 'st', 'nd', 'rd', 'th'

    print_settings('nthword: ' + nthword)

    try:
        int_output = int(nthword.strip(ordinal_ending_chars))
    except Exception as e:
        raise Exception('Illegal nth-word: ' + nthword)

    return int_output


def text2int(textnum):
    """Takes nuberic words (one, two, ninety) or ordinal words ("first",
    "thirteenth") and returns the number.
    It is from code found here: http://stackoverflow.com/a/598322/142780"""
    if not numwords:

        units = [
            'zero', 'one', 'two', 'three', 'four', 'five', 'six',
            'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve',
            'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen',
            'eighteen', 'nineteen']

        tens = [
            '', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty',
            'seventy', 'eighty', 'ninety']

        scales = [
            'hundred', 'thousand', 'million', 'billion', 'trillion',
            'quadrillion', 'quintillion', 'sexillion', 'septillion',
            'octillion', 'nonillion', 'decillion']

        numwords['and'] = (1, 0)
        for idx, word in enumerate(units):
            numwords[word] = (1, idx)
        for idx, word in enumerate(tens):
            numwords[word] = (1, idx * 10)
        for idx, word in enumerate(scales):
            numwords[word] = (10 ** (idx * 3 or 2), 0)

    ordinal_words = {
        'first': 1, 'second': 2, 'third': 3, 'fifth': 5, 'eighth': 8,
        'ninth': 9, 'twelfth': 12}
    ordinal_endings = [('ieth', 'y'), ('th', '')]
    current = result = 0
    tokens = re.split(r'[\s-]+', textnum)
    for word in tokens:
        if word in ordinal_words:
            scale, increment = (1, ordinal_words[word])
        else:
            for ending, replacement in ordinal_endings:
                if word.endswith(ending):
                    word = '%s%s' % (word[:-len(ending)], replacement)

            if word not in numwords:
                raise Exception('Illegal word: ' + word)

            scale, increment = numwords[word]

        if scale > 1:
            current = max(1, current)

        current = current * scale + increment
        if scale > 100:
            result += current
            current = 0

    return result + current


def map_feature_to_field(feature):
    """Takes a feature string and returns the corresponding database
    fieldname"""

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

    logger.debug('Feature to map: ' + feature)

    f = feature.lower()

    # NB: this structure assumes all features will be mapped by at least one of
    # the conditions below; if you have acceptable features that should be
    # passed through then some slight changes to the logic would be needed.

    if f in ('born', 'birth'):
        return 'DtBirth'
    if f in ('die', 'died', 'death'):
        return 'DtDeath'
    if f in ('cause of death'):
        return 'DeathCircumstances'
    if f == 'house':
        return 'House'
    if f in ('portrait', 'picture'):
        return 'Portrait'
    if f == 'title':
        return 'Title'
    if f in ('country', 'where'):
        return 'Country'
    if f in ('battle', 'battles'):
        return 'FamousBattles'
    if f in ('person', 'individual'):
        return 'Name'
    if f == 'number':
        return 'Number'
    # so we didn't match anything
    return None


def map_entity_to_number(ent):
    """Takes a complete entity and returns the corresponding number (as a
    string)"""

    logger.debug(
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
            print_settings('converting using nthwords2int')
            return str(nthwords2int(ent['value'].lower()))
        except:
            return None
    if etype in ('nth-words', 'number-words'):
        # TODO: Add better error and type checking
        try:
            return str(text2int(ent['value'].lower()))
        except:
            return None

    # so we couldn't match the etype to convert
    return None


def open_connection():
    """Opens the connection to the email service by use of the stored
    credentials"""

    # TODO: find a more sensible and secure approach or at least recommend
    # securing the credential file and add handling in the event of being
    # unable to read it.

    # Read the config file
    config = ConfigParser.ConfigParser()
    config.read([os.path.abspath(os.path.join('config', 'settings.ini'))])

    # Connect to the server
    hostname = config.get('server', 'imap-hostname')
    logger.debug('Connecting to ' + hostname)
    connection = imaplib.IMAP4_SSL(hostname, 993)

    # Login to our account
    username = config.get('account', 'username')
    password = config.get('account', 'password')
    logger.debug('Logging in as ' + username)
    connection.login(username, password)
    return connection


def get_msgs(subject=BOTNAME):
    """Gets all the messages that are unseen, with part of the subject matches
    the supplied subject (which defaults to be the bot name (BOTNAME)"""

    logger.debug('Checking messages')
    conn = open_connection()
    conn.select('INBOX')
    typ, data = conn.search(None, '(UNSEEN SUBJECT "%s")' % subject)
    for num in data[0].split():
        typ, data = conn.fetch(num, '(RFC822)')
        msg = email.message_from_string(data[0][1])
        typ, data = conn.store(num, 'FLAGS', '\\Seen')
        yield msg
    logger.debug('Logging out')
    conn.logout()


def get_sender(msg):
    """Trivial helper function to get the sender from an email message"""
    return msg['From']


def get_email_addr(sender):
    """Gets the pure email address (eg 'jdoe@example.com') from a sender
    (eg 'John Doe <jdoe@example.com') using a simplified regular expression"""

    # TODO: test how effective this is and whether there are many/any cases
    #      where it doesn't work
    expr = re.compile(r'[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}')
    return expr.findall(sender)[0]


def get_body(msg):
    """Gets the email body of a specified email message."""
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            body = part.get_payload(decode=True)
            return body.decode('utf-8')
        else:
            continue


def download_emails():
    """Obtains the new emails received by the email account configured for
    the bot, filtering to only respond to those sent by users on the safe list.
    An additional degree of basic filtering happens in the get_msgs function
    (eg to focus on new items with specific subject."""

    # CUSTOMISE: this can be left "as is" but if your bot has more involved
    # needs for exactly how it responds and to whom, then a re-write may be
    # needed.
    #
    # There is currently nothing present to allow following a conversation
    # 'thread' either, so each interaction is a one off with no concept of
    # prior conversation or information provided (so that may need to be added)

    logger.info('Checking emails')
    safe_list = ['nicolagcornish@aol.com', 'neil@nmstoker.com']
    lst = []
    for msg in get_msgs():
        sender = get_email_addr(get_sender(msg))
        if sender in safe_list:
            logger.debug('An email from: ' + sender)
            user_input = get_body(msg).split('\n')[0][:100]
            logger.debug('With first line: ' + user_input)
            lst.append({'user_input': user_input, 'sender': sender})
    return lst


def init():
    """Initialises the core functionality and sets up various globals."""
    global metadata
    global interpreter
    global db
    global cursor
    global rude_count
    global last_input
    global last_user_input
    global email_text
    global email_subject
    global email_list

    # TODO: add checks to confirm all necessary files are present and readable
    # (and writable if applicable)

    signal.signal(signal.SIGINT, handle_ctrl_c)

    logger.info('Initialisation started')
    metadata = json.loads(open(METADATA_LOCATION).read())
    interpreter = MITIEInterpreter(**metadata)
    db = sqlite3.connect(SQLITE_FILE)
    cursor = db.cursor()
    rude_count = 0
    last_input = {}
    last_user_input = None
    email_text = ''
    email_subject = ''
    email_list = []

    logger.info('Initialisation complete')


def say_text(text, greet=False):
    """Handles 'saying' the output, with different approaches depending on the
    active channel (or channels) for output"""
    if CHANNELS_OUT['screen']:
        if text[0] == '>':
            print(
                '\n\t\t' + STY_CURSOR + ' > ' + STY_USER + text[1:],
                end='  ' + STY_USER)
        else:
            print(
                '\n\t\t' + STY_RESP + '  ' + text,
                end='  ' + STY_USER + '\n\n')

    if CHANNELS_OUT['online']:
        LC_URL = LC_BASE_URL + '/messages'
        # We split on returns so that the entries get a new line (it's treated
        # as "code" entries otherwise :-( )
        for line in text.split('\n'):
            r = requests.post(
                LC_URL, auth=(LC_AUTH_TOKEN, 'xxx'), data={'text': line})

    if CHANNELS_OUT['email']:
        if greet is False:
            global email_text
            global email_subject
            if text[0] == '>':
                email_subject = BOTNAME + ' replying to your question - ' + \
                    text[1:].split('\n')[0]
                email_text = email_text + '> ' + text[1:].split('\n')[0] + '\n'
            else:
                email_text = email_text + text + '\n'


def store_email(mail_text):
    """Specifically logs the email content sent, as this is a potentially
    richer source than the basic intent history alone and it can be useful to
    retain who the recipient was as well."""
    with open(EMAIL_OUTPUT_FILE, "a") as f:
        f.write(str(mail_text) + '\n')


def send_email(address='test@nmstoker.com'):
    """Sends email via the configured email account to the address specified
    (with a fall-back of a safe non-end-user supplied email the default for
    'address'). Currently works with several globals (not ideal!)"""

    # TODO: fix this to not use globals (urggh!)
    global email_text
    global email_subject
    if not email_text.strip() == '':
        # Read the config file
        config = ConfigParser.ConfigParser()
        config.read([os.path.abspath('settings.ini')])

        # Connect to the server
        hostname = config.get('server', 'smtp-hostname')
        logger.debug('Connecting to ' + hostname)
        server = smtplib.SMTP(hostname, 587)
        server.ehlo()

        # Login to our account
        username = config.get('account', 'username')
        password = config.get('account', 'password')
        logger.debug('Logging in as ' + username)

        server.starttls()
        server.ehlo()
        server.login(username, password)

        fromaddr = username
        toaddr = address
        msg = MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg['Subject'] = email_subject
        msg.attach(MIMEText(email_text, 'plain', 'utf-8'))

        store_email(
            '----------\nTo: ' + address + '\nSubject: ' + email_subject +
            '\nContent:\n' + email_text)

        server.sendmail(username, [address], msg.as_string())
        server.quit()

        email_text = STY_EMAIL + 'EMAIL' + STY_USER + '\n' + msg.as_string()
        print(email_text)

    email_text = ''
    email_subject = ''


def print_settings(text):
    """A screen only output function for printing settings changes that do not
    go to remote users. Typically to give a more human friendly and detailed
    level than might be sent to the logs."""
    print(STY_DESC + text + STY_USER)


def handle_origin(resp):
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

    say_text(
        'I am ' + BOTNAME + ', a simple chatbot focused on basic ' +
        'questions regarding ' + BOTSUBJECT + '.\nI have been programmed ' +
        'in Python, using a machine learning backend that recognises user ' +
        'input and passes details to a script which in turn translates them ' +
        'so that relevant details can be accessed in a database, following ' +
        'which answers are constructed and given back to the user.')


def handle_example(resp):
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
        'Where did XXXXX happen?',
        'Who was XXXXX?',
        'Currently who is XXXXX?',
        'What date is XXXXX?',
        'What was the XXXXX?',
        'Tell me all about XXXXX',
        'What can I say?'
        ]

    suggestion_intro = random.choice([
        'Here\'s an example to try:\n\t',
        'How about this?\n\t',
        'Give this a go!\n\t'])

    say_text(suggestion_intro + ' "' + random.choice(example_list) + '"?')


def handle_deflect(resp):
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
    # it does with the substituted BOTSUBJECT alone (otherwise people *will*
    # notice it is clunky!)
    suggestion_list = [
        'How about asking me something about ' + BOTSUBJECT + '?',
        'Let\'s stick to questions about ' + BOTSUBJECT + '.',
        'We\'ll get further if we stick to ' + BOTSUBJECT +
        ' related questions.', 'My knowledge only really extends to matters' +
        ' related to ' + BOTSUBJECT + '.'
        ]

    say_text(
        random.choice(comment_list) + '\n\n' + random.choice(suggestion_list))


def handle_rude(resp):
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

    global rude_count
    rude_count = rude_count + 1

    if rude_count < 3:
        say_text(random.choice(replies_initial))
    else:
        say_text(random.choice(replies_more_direct))
        if rude_count > 5:
            rude_count = 0


def handle_help(resp):
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
        'I understand a handful of simple concepts related to ' + BOTSUBJECT +
        '.\n\nThere are various ways to select a particular row, such as ' +
        'the number (eg VI, 6 or sixth) or by a value (eg XXXXX).\n\n' +
        'Then you can pick out specific information such as:\n - Field1\n' +
        ' - Field2\n - Field3\n - Field4\n\nThen the ML magic happens, ' +
        'I try to understand what you\'ve said and then look up details ' +
        'based on entities recognised in a database.']
    say_text(random.choice(replies_initial))


def handle_demo(resp, show_parse):
    """Handles output of a series of demo inputs (automatically submitted in
    sequence) along with their responses. The inputs are read from a demo text
    file (one per line). To be effective the model must be trained for the
    inputs."""

    # -------------------------------------------------------------------------
    # CUSTOMISE DEMO_FILE CONTENTS TO THE PURPOSE OF THIS BOT (NO CHANGES
    # REQUIRED IN THE CODE HERE)
    # -------------------------------------------------------------------------

    demo_delay = 3
    print_settings('Running automated demo')
    for ent in resp['entities']:
        if ent['entity'].lower() == 'speed':
            if ent['value'].lower() in ['quick', 'fast']:
                demo_delay = 0
    prompt_text = '>'
    with open(DEMO_FILE, 'r') as f:
        for line in f:
            say_text(prompt_text + line)
            time.sleep(demo_delay)
            check_input(line, show_parse)
            time.sleep(demo_delay)

    print_settings('Automated demo complete')


def match_template(resp, fields, params):

    # TODO: finalise this function so the template is actually used for natural
    #      language generation in the output
    matching_templates = []

    templates = [
        {
            'intent': 'feature_example',
            'template_text': 'Template 1: Example $NUMBER'},
        {
            'intent': 'feature_example',
            'template_text': 'Template 2: Example $FEATURE'}
        ]

    for t in templates:
        if t['intent'] == resp['intent']:
            matching_templates.append(t)

    # TODO: put in a better 'fitness' selection process here!!
    chosen_template = random.choice(matching_templates)
    # TODO: put in the option to do substitution here (most likely scenario,
    #      barring edge cases)
    return chosen_template['template_text']


def handle_ruler_feature(resp,
                           detail=False,
                           overload_item=None,
                           verbose=False):
    logger.debug('Intent: ruler_feature')
    sql = 'SELECT {fields} FROM `ruler`'
    num = None
    loc = None
    fields = []
    where = []
    params = {}
    for ent in resp['entities']:
        if ent['entity'].lower() in (
                'name', 'location', 'number', 'number-words',
                'number-roman', 'nth-words', 'nth', 'title'):
            logger.info(
                'A selection entity was found: ' + ent['value'] +
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
                where.append('Country = :Location')
                params['Location'] = loc
            if ent['entity'].lower() in (
                    'number', 'number-roman', 'nth',
                    'nth-words', 'number-words'):
                num = map_entity_to_number(ent)
                if num is not None:
                    where.append('Number = :Number')
                    params['Number'] = num
        else:
            if not detail:
                logger.info(
                    'A field related entity was found: ' +
                    ent['value'] + ' (' + ent['entity'] + ')')
                f = map_feature_to_field(ent['value'])
                if f is not None:
                    fields.append(f)

    if overload_item is not None:
        where = ["Number = :Number"]
        params['Number'] = overload_item

    logger.debug('Fields: ' + str(fields))
    if overload_item is not None:
        logger.debug('Overload item: ' + str(overload_item))
    if loc is not None:
        logger.debug('Loc: ' + str(loc))
    if num is not None:
        logger.debug('Num: ' + str(num))
    if fields:
        sql = sql.format(fields=', '.join(fields))
    else:
        sql = sql.format(fields='*')
    if where:
        sql = '{} WHERE {}'.format(sql, ' AND '.join(where))
    logger.info('SQL: ' + sql)
    logger.info('Params: ' + str(params))
    cursor.execute(sql, params)
    output = ''
    results = cursor.fetchall()
    for row in results:
        output = ', '.join(row)
        say_text(output)
    if verbose is True:
        template = match_template(resp, fields, params)
        say_text(template)


def clean_input(u_input):
    """Fairly basic whirelisting based text cleaning function"""
    keepcharacters = (' ', '.', ',', ';', '\'')
    return ''.join(
        c for c in u_input if c.isalnum() or
        c in keepcharacters).rstrip()


def check_input(u_input, show_parse=False, verbose=False):
    """Checks the user supplied input and passes it to the Rasa NLU model to
    get the intent and entities"""
    global last_input
    logger.debug('User input: ' + u_input)
    u_input = clean_input(u_input)
    logger.debug('User input (cleaned): ' + u_input)
    if len(u_input) == 0:
        logger.debug('Skipping empty input')
        return
    resp = interpreter.parse(u_input)
    if show_parse:
        print_settings('\tParse output:\n\t\t' + str(resp))
    last_input = resp
    if 'intent' in resp:
        # ---------------------------------------------------------------------
        # THIS IS WHERE YOU UPDATE THE CUSTOM INTENTS THAT YOU HAVE TRAINED
        # RASA NLU TO HANDLE
        # ---------------------------------------------------------------------
        #
        # Depending on need you may wish to keep the fairly generic ones
        # (esp help, deflect), but remember that your model has to be trained
        # for them specifically (ie returns an intent of 'help' or 'deflect' or
        # whatever it may be)
        #
        # ---------------------------------------------------------------------
        if resp['intent'] == 'ruler_feature':
            # the "handle_{intent name}" is merely a convention for
            # readibility; they could just as well be called any acceptable
            # function name (for Python) that you like but try to keep the
            # meaning clear if possible.
            handle_ruler_feature(resp, False, verbose=verbose)
        elif resp['intent'] == 'detail_example':
            # in some scenarios it might be useful to re-use the same intent
            # handling but passing a distinct parameter
            handle_ruler_feature(resp, True)
        elif resp['intent'] == 'rude':
            handle_rude(resp)
        elif resp['intent'] == 'deflect':
            handle_deflect(resp)
        elif resp['intent'] == 'help':
            handle_help(resp)
        elif resp['intent'] == 'example':
            handle_example(resp)
        elif resp['intent'] == 'origin':
            handle_origin(resp)
        elif resp['intent'] == 'demo':
            handle_demo(resp, show_parse)
        else:
            say_text(
                'Intent ' + resp['intent'] + ' is recognsied but I do ' +
                'not have the necessary skills to respond appropriately. ' +
                'Sorry!')
    else:
        logger.info('Sorry, no intent recognised...')


def before_quit():
    """Does any required closinng of resources prior to the programme quiting
    and then reports end of script execution"""
    try:
        cursor.close()
    except NameError:
        print('')
    try:
        db.close()
    except NameError:
        print('')
    try:
        logger.warn('Ending script execution now\n')
    except NameError:
        print('Ending script execution now\n(logger was not found.)\n')
    sys.exit()


def greeting():
    """Outputs to the user the basic greeting at startup."""
    say_text('Hello! I\'m ' + BOTNAME + '.', greet=True)


def tag_last():
    """Ouputs tagged items (ie responses of some particular interest, typically
    due to an error) to a file"""
    print_settings('Tagged: ' + str(last_input))
    with open(TAGGED_OUTPUT_FILE, "a") as f:
        f.write(str(last_input) + '\n')


def poll_LC():
    """Polls the Let's Chat room associated with the bot for any new
    messages"""
    LC_URL = LC_BASE_URL + '/messages?take=1'
    user_input = ''
    global last_user_input
    while True:
        time.sleep(LC_POLLING_TIME)
        try:
            r = requests.get(LC_URL, auth=(LC_AUTH_TOKEN, 'xxx'))
            logger.debug(r.text)
            if r.json()[0]['owner'] in LC_USER_FILTER:
                logger.debug('Owner matches: ' + str(r.json()[0]['owner']))
                user_input = r.json()[0]['text']
                if (user_input[0:4] != 'http') & \
                        (user_input != last_user_input):
                    if last_user_input:
                        last_user_input = user_input
                        logger.debug('We have a new input')
                        logger.debug('user_input is: ' + user_input)
                        break
                    else:
                        last_user_input = user_input
        except:
            logger.warn('Error in poll_LC' + str(sys.exc_info()[0]))
    logger.debug('Returning  user_input: ' + user_input)
    return user_input


def poll_email():
    """Polls the list of unprocessed emails and if there aren't any it will
    check the email account directly"""
    global email_list
    # TODO: look into better performance versions of this (pop(0) isn't great
    #      apparently)
    if len(email_list) > 0:
        prompt_text = '>'
        email_item = email_list.pop(0)
        say_text(prompt_text + email_item['user_input'] + '\n')
        return email_item
    else:
        time.sleep(30)
        email_list.extend(download_emails())
        return None


def main_loop():
    """The main loop which repeats continuously until the programme is aborted
    or a crash occurs. It cycles round seeking input from which ever of the
    particular input modes the bot is configured to handle.
    It also handles low-level commands prior to passing input to Rasa NLU, such
    as toggling 'show parse' (s), tagging output (t), toggling verbose output,
    changing logging level (d=DEBUG, i=INFO , w=WARN) or quiting (q)"""
    show_parse = False
    verbose = False
    if os.path.exists(HISTORY_FILENAME):
        readline.read_history_file(HISTORY_FILENAME)
    prompt_text = STY_CURSOR + ' > ' + STY_USER
    try:
        while True:
            if CHANNEL_IN == 'online':
                user_input = poll_LC()
            elif CHANNEL_IN == 'email':
                email_item = poll_email()
                if email_item is None:
                    user_input = ''
                else:
                    user_input = email_item['user_input']
            else:  # screen
                user_input = raw_input(prompt_text)
            print(style.RESET, end="")
            if user_input.lower() == 'q':
                print(
                    '\t\t' + STY_RESP + '  Okay.  Goodbye!  ' + STY_USER +
                    '\n')
                before_quit()
            elif user_input.lower() == 't':
                tag_last()
            elif user_input.lower() == 'v':
                verbose = not verbose
                print_settings('Verbose responses: ' + str(verbose))
            elif user_input.lower() == 's':
                show_parse = not show_parse
                print_settings(
                    'Show_parse: ' + {True: 'on', False: 'off'}[show_parse])
            elif user_input.lower() == 'd':
                ch.setLevel(logging.DEBUG)
                logger.info('Logging level set to DEBUG')
            elif user_input.lower() == 'i':
                ch.setLevel(logging.INFO)
                logger.info('Logging level set to INFO')
            elif user_input.lower() == 'w':
                ch.setLevel(logging.WARNING)
                logger.warn('Logging level set to WARN')
            else:
                check_input(user_input, show_parse, verbose)
            if CHANNELS_OUT['email']:
                if email_item is not None:
                    send_email(email_item['sender'])
    finally:
        readline.write_history_file(HISTORY_FILENAME)


if __name__ == '__main__':
    init()
    greeting()
    main_loop()
