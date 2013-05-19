# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

from __future__ import with_statement

import sys, re

import oktest
from oktest import ok, not_ok, spec
from oktest.helper import using
import keight as k8


class UtilsTest(object):

    INPUT1  = 'http://example.com/~user/?x[]=b'
    QUOTED1 = 'http%3A//example.com/%7Euser/%3Fx%5B%5D%3Db'


with using(UtilsTest):

    def test_quote(self):
        with spec("converts symbols into '%XX'"):
            ok (k8.quote(self.INPUT1)) == self.QUOTED1
        with spec("if input contains spaces then convert them into '%20'"):
            ok (k8.quote(' +  ')) == '%20%2B%20%20'

    def test_quote_plus(self):
        with spec("converts symbols into '%XX'"):
            ok (k8.quote_plus(self.INPUT1)) == self.QUOTED1
        with spec("if input contains spaces then convert them into '+'"):
            ok (k8.quote_plus(' +  ')) == '+%2B++'

    def test_unquote_plus(self):
        from keight import unquote_plus
        with spec("converts '%XX' into original string"):
            ok (unquote_plus('%5B%5D')) == '[]'
            ok (unquote_plus('%5b%5d')) == '[]'
        with spec("if failed to convert then returns as is"):
            ok (unquote_plus('%5B%%%_0%5D')) == '[%%%_0]'
        with spec("if upper and lower cases are mixed then ignores case"):
            v = unquote_plus('%FF')
            ok (unquote_plus('%Ff')) == v
            ok (unquote_plus('%fF')) == v
        with spec("if '%' is appreared at the beginning/end of string then handled correctly"):
            ok (unquote_plus('%_')) == '%_'
            ok (unquote_plus('%5b%')) == '[%'
            ok (unquote_plus('%')) == '%'
        with spec("if '+' is included then converts it as ' '"):
            ok (unquote_plus('+')) == ' '


if __name__ == '__main__':
    oktest.run()
