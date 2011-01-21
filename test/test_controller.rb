# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

require "#{File.dirname(__FILE__)}/_setup"



class ControllerTest
  include Oktest::TestCase

  class Dummy1 < K8::Controller
  end

  def test_self_inhrerited
    spec "subclass will be set Router object." do
      obj = Dummy1.instance_variable_get('@_router')
      ok_(obj).is_a?(K8::Router)
      ok_(Dummy1.router).same? obj
    end
    spec "subclass will be set Actions object." do
      obj = Dummy1.instance_variable_get('@_actions')
      ok_(obj).is_a?(K8::Actions)
      ok_(Dummy1.actions).same? obj
    end
    spec "subclass will be defined base_path() method." do
      ok_(Dummy1.instance_variable_get('@_base_path')) == nil
      Dummy1.base_path = '/books'
      ok_(Dummy1.instance_variable_get('@_base_path')) == '/books'
      ok_(Dummy1.base_path) == '/books'
    end
  end

#   def test_self_method_added
#     spec "if @_metadata is not set then do nothing." do
#       Dummy1.class_eval do
#         def hello; return "Hello"; end
#       end
#       ok_(Dummy1.actions.instance_variables) == ['@controller_class']
#     end
#     spec "if @_metadata is set..." do
#       Dummy1.class_eval do
#         @_metadata = K8::ActionMetadata.new(Dummy1, :SOS, '/sos', [])
#         def do_hello2; return "Hello2"; end
#       end
#       spec "register metadata into @_actions." do
#         ok_(Dummy1.actions.instance_variables.sort) == ['@controller_class', '@hello2'].sort
#         ok_(Dummy1.actions.hello2).is_a?(K8::ActionMetadata)
#       end
#       spec "map path_pattern, request_method, and action_method to @_router." do
#         ok_(Dummy1.router.route('/sos', :SOS)) == [:do_hello2, []]
#       end
#       spec "set action_method and action_name to metadata." do
#         metadata = Dummy1.actions.hello2
#         ok_(metadata.action_method) == :do_hello2
#         ok_(metadata.action_name) == :hello2
#       end
#       spec "clear @_metadata." do
#         ok_(Dummy1.class_eval { @_metadata }) == nil
#       end
#     end
#   end


  class Dummy2 < K8::Controller
    GET('/')
    def index
    end
  end

  def test_actions
    c = Dummy2.new(nil, nil)
    ok_(c.actions).is_a?(K8::Actions)
    ok_(c.actions).same? Dummy2.actions
  end


  class Dummy3 < K8::Controller
    self.base_path = '/books'
    GET('/')
    def do_index
      "do_index()"
    end
    POST('/', :admin, :csrf)
    def create
      "do_create()"
    end
    GET('/new', :admin)
    def new
      "do_new()"
    end
    GET('/<id>')
    def show(id)
      "do_show(#{id.inspect})"
    end
    PUT('/<id>', :admin, :csrf=>false)
    def do_update(id)
      "do_update(#{id.inspect})"
    end
    DELETE('/<id>', :admin, :csrf=>true)
    def delete(id)
      "do_delete(#{id.inspect})"
    end
    GET('/<id>/edit', :admin)
    def edit(id)
      "do_edit(#{id.inspect})"
    end
    GET('/raise_error')
    def raise_error
      nil.foobar
    end
  end

  def _c3(*args)
    env = K8::Debug::dummy_env(*args)
    return Dummy3.new(K8::Request.new(env), K8::Response.new)
  end

  def test_FUNCTEST_restful
    ok_(_c3('GET', '/books/').handle)          == 'do_index()'
    ok_(_c3('POST', '/books/').handle)         == 'do_create()'
    ok_(_c3('GET', '/books/new').handle)       == 'do_new()'
    ok_(_c3('GET', '/books/123').handle)       == 'do_show("123")'
    ok_(_c3('PUT', '/books/123').handle)       == 'do_update("123")'
    ok_(_c3('DELETE', '/books/123').handle)    == 'do_delete("123")'
    ok_(_c3('GET', '/books/123/edit').handle)  == 'do_edit("123")'
    #
    c = _c3('GET', '/books/new1')
    ok_(c.handle) == <<'END'
<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>404 Not Found</title>
</head><body>
<h1>404 Not Found</h1>
<p>/books/new1: not found.</p>
</body></html>
END
    ok_(c.response.status_code) == 404
    c = _c3('POST', '/books/123')
    ok_(c.handle) == <<'END'
<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>405 Method Not Allowed</title>
</head><body>
<h1>405 Method Not Allowed</h1>
<p>POST: method not allowed.</p>
</body></html>
END
    ok_(c.response.status_code) == 405
    c = _c3('GET', '/books/raise_error')
    ok_(c.handle) =~ %r|^<h2>500 Internal Server Error</h2>$|
    ok_(c.response.status_code) == 500
    #
    c = _c3(:GET, nil)
    ok_(c.actions.index.path)       == '/books/'
    ok_(c.actions.create.path)      == '/books/'
    ok_(c.actions.new.path)         == '/books/new'
    ok_(c.actions.show.path(999))   == '/books/999'
    ok_(c.actions.update.path(999)) == '/books/999'
    ok_(c.actions.delete.path(999)) == '/books/999'
    ok_(c.actions.edit.path(999))   == '/books/999/edit'
    #
    ok_(c.actions.index.method)  == :GET
    ok_(c.actions.create.method) == :POST
    ok_(c.actions.new.method)    == :GET
    ok_(c.actions.show.method)   == :GET
    ok_(c.actions.update.method) == :PUT
    ok_(c.actions.delete.method) == :DELETE
    ok_(c.actions.edit.method)   == :GET
    #
    ok_(c.actions.index.method)  == :GET
    ok_(c.actions.create.method) == :POST
    ok_(c.actions.new.method)    == :GET
    ok_(c.actions.show.method)   == :GET
    ok_(c.actions.update.method) == :PUT
    ok_(c.actions.delete.method) == :DELETE
    ok_(c.actions.edit.method)   == :GET
    #
    ok_(c.actions.index.options)  == {}
    ok_(c.actions.create.options) == {:admin=>true, :csrf=>true}
    ok_(c.actions.new.options)    == {:admin=>true}
    ok_(c.actions.show.options)   == {}
    ok_(c.actions.update.options) == {:admin=>true, :csrf=>false}
    ok_(c.actions.delete.options) == {:admin=>true, :csrf=>true}
    ok_(c.actions.edit.options)   == {:admin=>true}
  end

end
