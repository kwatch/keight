# -*- coding: utf-8 -*-

import sys, os, re, shutil
from datetime import datetime

import oktest
from oktest import ok, test, skip, todo, subject, situation, at_end

import keight as k8
from keight import on



class On_Test(object):


    with subject('#path()'):

        @test("[!nhlhs] works with 'with' statement.")
        def _(self):
            ok (on._urlpath_pattern) == None
            with on.path('/foo/{id}'):
                ok (on._urlpath_pattern) == '/foo/{id}'
            ok (on._urlpath_pattern) == None

        @test("[!fl2hd] (UNDOCUMENTED) allows to nest 'with' statement.")
        def _(self):
            ok (on._urlpath_pattern) == None
            with on.path('/foo'):
                ok (on._urlpath_pattern) == '/foo'
                with on.path('/{id}'):
                    ok (on._urlpath_pattern) == '/foo/{id}'
                    with on.path('/comments'):
                        ok (on._urlpath_pattern) == '/foo/{id}/comments'
                    ok (on._urlpath_pattern) == '/foo/{id}'
                ok (on._urlpath_pattern) == '/foo'
            ok (on._urlpath_pattern) == None



if __name__ == '__main__':
    import oktest
    oktest.main()
