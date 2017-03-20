# -*- coding: utf-8 -*-
import re
import os
import logging
from colored import fore, back, style


STY_DESC = fore.LIGHT_GREEN + back.BLACK
STY_DESC_DEBUG = fore.SKY_BLUE_1 + back.BLACK + style.DIM
STY_USER = style.RESET + fore.WHITE + back.BLACK
STY_CURSOR = fore.LIGHT_GOLDENROD_2B + back.BLACK + style.BOLD
STY_RESP = fore.WHITE + back.MEDIUM_VIOLET_RED + style.BOLD
# STY_RESP = fore.WHITE + back.GREY_11 + style.BOLD #+ style.NORMAL
STY_EMAIL = fore.WHITE + back.GREY_11 + style.BOLD


def setup_custom_logger(name):
    formatter = logging.Formatter(
        STY_DESC_DEBUG + '%(asctime)s - %(module)s - %(levelname)8s - %(message)s' +
            style.RESET, datefmt='%Y-%b-%d %H:%M:%S')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.WARN)
    logger.addHandler(handler)
    return logger

    # self.logger = logging.getLogger(self.BOTNAME)
    # self.logger.setLevel(logging.DEBUG)

    # self.ch.setLevel(logging.WARN)
    # # ch.setLevel(logging.DEBUG)
    # self.ch.setFormatter(self.formatter)
    # self.logger.addHandler(self.ch)


def clear_screen():
    """Simple cross-platform way to clear the terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')


def nthwords2int(nthword):
    """Takes an "nth-word" (eg 3rd, 21st, 28th) strips off the ordinal ending
    and returns the pure number."""

    ordinal_ending_chars = 'stndrh'  # from 'st', 'nd', 'rd', 'th'

    try:
        int_output = int(nthword.strip(ordinal_ending_chars))
    except Exception as e:
        raise Exception('Illegal nth-word: ' + nthword)

    return int_output


def text2int(textnum, numwords={}):
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
 

def clean_input(u_input):
    """Fairly basic whitelisting based text cleaning function"""
    keepcharacters = (' ', '.', ',', ';', '\'', '?', '-')
    return ''.join(
        c for c in u_input if c.isalnum() or
        c in keepcharacters).rstrip()
