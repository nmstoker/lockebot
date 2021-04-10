#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import actions
import unittest 

class NthWords2IntKnownValues(unittest.TestCase):
    # TODO: add additional test case values here
    known_values = ( ('3rd', 3),
                     ('21st', 21),
                     ('28th', 28))

    def test_nthwords2int_known_values(self):           
        '''nthwords2int should give known result with known input'''
        for string, integer in self.known_values:
            result = actions.nthwords2int(string)       
            self.assertEqual(integer, result)       


if __name__ == '__main__':
    unittest.main()
