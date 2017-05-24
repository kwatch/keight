# -*- coding: utf-8 -*-

import sys, os, re, shutil
from datetime import datetime

import oktest
from oktest import ok, test, skip, todo, subject, situation, at_end

import keight as k8
from keight import PY2, PY3

if PY3:
    xrange = range



class misc_Test(object):

    def provide_dummies(self, basedir):
        self._basedir = basedir
        os.makedirs(basedir + "/foo/bar")
        at_end(lambda: shutil.rmtree(self._basedir))
        touch = lambda x: open(x, 'w').close()
        touch(basedir + "/__init__.py")
        touch(basedir + "/foo/__init__.py")
        touch(basedir + "/foo/bar/__init__.py")
        touch(basedir + "/foo/bar/baz.py")
        with open(basedir + "/foo/bar/hello.py", 'w') as f:
            f.write("class Hello(object):\n")
            f.write("  def hello(self):\n")
            f.write("    return 'Hello, world!'\n")


    with subject('_create_module()'):

        @test("[!dacsh] creates new module object and returns it.")
        def _(self):
            mod_name = "test_dacsh.foo"
            mod = k8._create_module(mod_name, X=1, Y=2)
            ok (mod).is_a(type(sys))
            ok (mod.__name__) == mod_name
            ok (mod).attr('X', 1).attr('Y', 2)

        @test("[!0k2on] registers module object created into sys.modules.")
        def _(self):
            mod_name = "test_chxlz.bar.baz"
            ok (mod_name).not_in(sys.modules)
            k8._create_module(mod_name)
            ok (mod_name).in_(sys.modules)


    with subject('_load_module()'):

        @test("[!z4rh2] returns the child module object instead of parent module.")
        def _(self, dummies, basedir="test_z4rh2"):
            ok (basedir + ".foo.bar").not_in(sys.modules)
            mod_bar = k8._load_module(basedir + ".foo.bar")
            ok (mod_bar).is_a(type(sys))
            ok (mod_bar.__name__) == basedir + ".foo.bar"
            ok (basedir + ".foo.bar").in_(sys.modules)
            #
            ok (basedir + ".foo.bar.baz").not_in(sys.modules)
            mod_baz = k8._load_module(basedir + ".foo.bar.baz")
            ok (mod_baz).is_a(type(sys))
            ok (mod_baz.__name__) == basedir + ".foo.bar.baz"
            ok (basedir + ".foo.bar.baz").in_(sys.modules)


    with subject('_load_class()'):

        @test("[!xkimv] loads module object which contains Class object.")
        def _(self, dummies, basedir="test_xkimv"):
            ok (basedir + ".foo.bar.hello").not_in(sys.modules)
            k8._load_class(basedir + ".foo.bar.hello.Hello")
            ok (basedir + ".foo.bar.hello").in_(sys.modules)

        @test("[!9nvnz] returns class object.")
        def _(self, dummies, basedir="test_9nvnz"):
            cls = k8._load_class(basedir + ".foo.bar.hello.Hello")
            ok (cls).is_a(type(self.__class__))
            ok (cls.__name__) == "Hello"

        @test("[!jq5wu] returns None when class not found.")
        def _(self, dummies, basedir="test_jq5wu"):
            cls = k8._load_class(basedir + ".foo.bar.hello.XXX")
            ok (cls) == None

        @test("[!hwvc4] finds class object from globals when no module specified.")
        def _(self):
            cls = k8._load_class("ValueError")
            ok (cls).is_(ValueError)



if __name__ == '__main__':
    import oktest
    oktest.main()
