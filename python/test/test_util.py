# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

import sys, re

import oktest
from oktest import ok, not_ok
import keight as k8


class K8UtilsTest(object):

    def test_unquote_plus(self):
        from keight import unquote_plus
        if "called then converts '%XX' into original string":
            ok (unquote_plus('%5B%5D')) == '[]'
            ok (unquote_plus('%5b%5d')) == '[]'
        if "not able to convert then returns as is":
            ok (unquote_plus('%5B%%%_0%5D')) == '[%%%_0]'
        if "upper and lower cases are mixed then ignores case":
            v = unquote_plus('%FF')
            ok (unquote_plus('%Ff')) == v
            ok (unquote_plus('%fF')) == v
        if "'%' is appreared at the beginning/end of string then handled correctly":
            ok (unquote_plus('%_')) == '%_'
            ok (unquote_plus('%5b%')) == '[%'
            ok (unquote_plus('%')) == '%'
        if "'+' is included then converts it as ' '":
            ok (unquote_plus('+')) == ' '


if __name__ == '__main__':
    oktest.run(K8UtilsTest)
