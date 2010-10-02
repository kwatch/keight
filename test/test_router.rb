# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

require "#{File.dirname(__FILE__)}/_setup"


class RouterTest
  include Oktest::TestCase

  def _rexp_mappings(router)
    router.instance_variable_get('@rexp_mappings')
  end

  def _fixed_mappings(router)
    router.instance_variable_get('@fixed_mappings')
  end

  def test_init
  end

  def test_map
    spec "if hash key is String then converts it into Symbol." do
      r = K8::Router.new
      r.map('/', 'GET' => :do_index)
      ok_(_fixed_mappings(r)['/']) == {:GET=>:do_index}
    end
    spec "if path_pattern doesn't start with '/' then raise error, except empty path." do
      r = K8::Router.new
      msg = "\"new\": expected to start with '/'."
      ok_(proc { r.map('new', :GET => :do_index) }).raise?(RuntimeError, msg)
      not_ok_(proc { r.map('', :GET => :do_index) }).raise?(Exception)
    end
    spec "if path_pattern contains '<...>'..." do
      r = K8::Router.new
      spec "if path pattern is not added yet then add new tuples as regexp mapping." do
        _rexp_mappings(r) == []  or raise "ERROR"
        r.map('/<id>', :GET=>:do_show, :PUT=>:do_update)
        #ok_(_rexp_mappings(r)) == [ ['/<id>', /\A\/(\d+)\z/, {:GET=>:do_show, :PUT=>:do_update}] ]
        ok_(_rexp_mappings(r)) == [ ['/<id>', %r|\A/(\d+)\z|, {:GET=>:do_show, :PUT=>:do_update}] ]
      end
      spec "if path_pattern is already added then append req_method and action_method to existing hash object." do
        #falldown
        r.map('/<id>', :DELETE=>:do_delete)
        ok_(_rexp_mappings(r)) == [ ['/<id>', %r|\A/(\d+)\z|, {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete}] ]
      end
    end
    spec "if path_pattern doesn't contain '<...>' then add them as fixed mapping." do
      r = K8::Router.new
      r.map('/new', :GET=>:do_new)
      ok_(_fixed_mappings(r)) == { '/new' => {:GET=>:do_new} }
    end
    spec "return self." do
      r = K8::Router.new
      ok_(r.map('/new', :GET=>:do_new)).same?(r)
    end
  end

  def test_route
    spec "fixed mapping is prior to rexp mapping." do
      r = K8::Router.new
      r.map('/<id>', :GET=>:show)
      r.map('/123', :GET=>:show2)
      ok_(r.route('/123', :GET)) == [:show2, []]
    end
    spec "if matched to fixed mapping..." do
      spec "if req_method is not matched then check :ALL." do
        r = K8::Router.new
        r.map('/', :GET=>:index, :ALL=>:index2)
        ok_(r.route('/', :POST)) == [:index2, []]
      end
      spec "if neight req_method nor :ALL matched then returns false." do
        r = K8::Router.new
        r.map('/', :GET=>:index)
        ok_(r.route('/', :POST)) == [false, []]
      end
      spec "args is always empty if matched to fixed mapping." do
        r = K8::Router.new
        r.map('/', :GET=>:index)
        ok_(r.route('/', :GET)) == [:index, []]
        ok_(r.route('/', :PUT)) == [false, []]
      end
    end
    spec "if not matched to fixed mapping..." do
      spec "if req_method is not matched then check :ALL." do
        r = K8::Router.new
        r.map('/<id>', :GET=>:show, :ALL=>:show2)
        ok_(r.route('/123', :POST)) == [:show2, ['123']]
      end
      spec "if neight req_method nor :ALL matched then returns false." do
        r = K8::Router.new
        r.map('/<id>', :GET=>:show)
        ok_(r.route('/123', :POST)) == [false, ['123']]
      end
      spec "catpured values are returned as args." do
        r = K8::Router.new
        r.map('/<date:(\d\d)\-(\d\d)>', :GET=>:show)
        ok_(r.route('/12-31', :GET)) == [:show, ['12', '31']]
      end
      spec "return nil if not matched." do
        r = K8::Router.new
        r.map('/<id>', :GET=>:show)
        ok_(r.route('/new', :GET)) == [nil, nil]
      end
    end
  end

  def test__path_pattern_rexp
    K8::Router::COMPILED__.clear()
    r = K8::Router.new
    spec "if path_pattern already exists in cache then return it." do
      K8::Router::COMPILED__['/dummy'] = "DUMMY"
      ok_(r.send(:_path_pattern_rexp, '/dummy')) == "DUMMY"
    end
    spec "if path_pattern doesn't exist in cache then compile and cache it." do
      ok_(r.send(:_path_pattern_rexp, '/<id>')) == %r|\A/(\d+)\z|
    end
  end

  def test__compile_path_pattern
    r = K8::Router.new
    spec "escape strings which is on outside of '<...>'." do
      ok_(r.send(:_compile_path_pattern, '/<id>(.html)?')) == %r|\A/(\d+)\(\.html\)\?\z|
    end
    spec "'<id>' is regarded as '<id:(\d+)>'." do
      ok_(r.send(:_compile_path_pattern, '/<id>')) == %r|\A/(\d+)\z|
    end
    spec "remove label name ('xxx:') from pattern." do
      ok_(r.send(:_compile_path_pattern, '/<ymd:(\d\d\d\d)\-(\d\d)\-(\d\d)>')) == %r|\A/(\d\d\d\d)\-(\d\d)\-(\d\d)\z|
    end
    spec "if path_pattern doesn't contain '<...>' then return nil." do
      ok_(r.send(:_compile_path_pattern, '/(\d+)')) == nil
    end
    spec "if path_pattern contains '<...>' then return Regexp." do
      ok_(r.send(:_compile_path_pattern, '/<(\d+)>')).is_a?(Regexp)
    end
  end


end
