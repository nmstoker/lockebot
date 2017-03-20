#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import roybot
import util as u
import unittest 

class NthWords2IntKnownValues(unittest.TestCase):
    # TODO: add additional test case values here
    known_values = ( ('3rd', 3),
                     ('21st', 21),
                     ('28th', 28))

    def test_nthwords2int_known_values(self):           
        '''nthwords2int should give known result with known input'''
        for string, integer in self.known_values:
            result = u.nthwords2int(string)       
            self.assertEqual(integer, result)       


class Text2IntKnownValues(unittest.TestCase):
    # TODO: add additional test case values here
    known_values = ( ('first', 1),
                     ('second', 2),
                     ('third', 3),
                     ('fourth', 4),
                     ('fifth', 5),
                     ('sixth', 6),
                     ('seventh', 7),
                     ('eighth', 8),
                     ('ninth', 9),
                     ('tenth', 10),
                     ('eleventh', 11),
                     ('one', 1),
                     ('two', 2),
                     ('three', 3))

    def test_text2int_known_values(self):           
        '''text2int should give known result with known input'''
        for textnum, integer in self.known_values:
            result = u.text2int(textnum)       
            self.assertEqual(integer, result)       


class CleanInputKnownValues(unittest.TestCase):
    # TODO: add additional test case values here
    # look at naughty-string list for inspiration on cases
    # https://github.com/minimaxir/big-list-of-naughty-strings/blob/master/blns.txt
    known_values = ( ('Nothing unusual here.', 'Nothing unusual here.'),
                     ("He's over there!", "He's over there"),
                     (',./;\'[]\-=', ',.;\''),
                     ('<>?:"{}|_+', ''),
                     ('', ''),
                     ('AΩ≈ç√∫˜µ≤≥B÷', 'AB'))


    def test_clean_input_known_values(self):           
        '''clean_input should give known result with known input'''
        for u_input, expected_output in self.known_values:
            result = u.clean_input(u_input)       
            self.assertEqual(expected_output, result)       


class SayTextKnownValues(unittest.TestCase):
    # TODO: add additional test case values here
    prefix = '\x1b[38;5;15m\x1b[48;5;126m\x1b[1m  '
    suffix = '  \x1b[0m\x1b[38;5;15m\x1b[48;5;0m'

    known_values = ( ('hello', False, prefix + 'hello' + suffix),
                     ('Something strange', False, prefix + 'Something strange' + suffix),
                     ('What?\n', False, prefix + 'What?\n' + suffix))

    def test_say_text(self):           
        '''say_text should give known result with known input'''
        from StringIO import StringIO

        for text, greet, expected_output in self.known_values:
            out = StringIO()
            roybot.say_text(text, greet, out=out)
            result = out.getvalue().strip()
            self.assertEqual(expected_output, result)       


if __name__ == '__main__':
    unittest.main()
