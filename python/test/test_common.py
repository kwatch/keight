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
import keight as k8


class CommonUtilsTest(object):
    pass


with oktest.using(CommonUtilsTest):

    def test_new_cycle(self):
        with spec("returns cycle object"):
            cycle = k8.new_cycle('odd', 'even')
            ok (cycle()) == 'odd'
            ok (cycle()) == 'even'
            ok (cycle()) == 'odd'
            ok (cycle()) == 'even'

    def test_each_slice(self):
        arr = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']
        with spec("returns generator object"):
            generator_type = type(x for x in [1])
            ok (k8.each_slice([1], 1)).is_a(generator_type)
        with spec("yields with n-items"):
            g = k8.each_slice(arr, 3)
            ok (list(g)) == [['a','b','c'], ['d','e','f'], ['g','h','i']]
        with spec("if pad is not specified then length of last items can be less than n"):
            g = k8.each_slice(arr, 4)
            ok (list(g)) == [['a','b','c','d'], ['e','f','g','h'], ['i']]
        with spec("if pad is specified then padded by it and lenght of last items is equal to n"):
            g = k8.each_slice(arr, 4, None)
            ok (list(g)) == [['a','b','c','d'], ['e','f','g','h'], ['i', None, None, None]]


if __name__ == '__main__':
    oktest.run(CommonUtilsTest)
