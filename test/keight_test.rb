# -*- coding: utf-8 -*-

$LOAD_PATH << "lib"  unless $LOAD_PATH.include?("lib")
$LOAD_PATH << "test" unless $LOAD_PATH.include?("test")

require 'oktest'

require 'keight'


class BooksAction < K8::Action
  mapping '/',      :GET=>:do_index, :POST=>:do_create
  mapping '/new',   :GET=>:do_new
  mapping '/{id}',  :GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete
  mapping '/{id}/edit', :GET=>:do_edit
  #
  def do_index();    "<index>";  end
  def do_create();   "<create>"; end
  #def do_new();      "<new>";    end
  def do_show(id);   "<show:#{id.inspect}(#{id.class})>";   end
  def do_update(id); "<update:#{id.inspect}(#{id.class})>"; end
  def do_delete(id); "<delete:#{id.inspect}(#{id.class})>"; end
  def do_edit(id);   "<edit:#{id.inspect}(#{id.class})>";   end
end

class BookCommentsAction < K8::Action
  mapping '/comments',                :GET=>:do_comments
  mapping '/comments/{comment_id}',   :GET=>:do_comment
  #
  def do_comments(); "<comments>"; end
  def do_comment(comment_id); "<comment:#{comment_id}>"; end
end


class AdminBooksAction < K8::Action
  mapping '/',      :GET=>:do_index, :POST=>:do_create
  mapping '/new',   :GET=>:do_new
  mapping '/{id}',  :GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete
  mapping '/{id}/edit', :GET=>:do_edit
  #
  def do_index(); end
  def do_create(); end
  def do_show(id); end
  def do_update(id); end
  def do_delete(id); end
  def do_edit(id); end
end


class TestBaseAction < K8::BaseAction
  def _called
    @_called ||= []
  end
  def before_action(*args)
    self._called << ["before_action", args]
  end
  def after_action(*args)
    self._called << ["after_action", args]
  end
  def handle_content(*args)
    self._called << ["handle_content", args]
    super(*args)
  end
  def do_index
    return "<index>"
  end
  def do_create
    1/0   #=> ZeroDivisionError
  end
  def do_show(id)
    return "<show:#{id}>"
  end
end


Oktest.scope do

  def new_env(meth="GET", path="/", headers={})
    env = {
      "REQUEST_METHOD" => meth,
      "PATH_INFO"      => path,
      "SCRIPT_NAME"    => "",
      "QUERY_STRING"   => "",
      "SERVER_NAME"    => "localhost",
      "SERVER_PORT"    => "80",
    }
    env.update(headers)
    return env
  end


  topic K8::Util do


    topic '.parse_query_string()' do

      spec "[!fzt3w] parses query string and returns Hahs object." do
        d = K8::Util.parse_query_string("x=123&y=456&z=")
        ok {d} == {"x"=>"123", "y"=>"456", "z"=>""}
      end

      spec "[!engr6] returns empty Hash object when query string is empty." do
        d = K8::Util.parse_query_string("")
        ok {d} == {}
      end

      spec "[!t0w33] regards as array of string when param name ends with '[]'." do
        d = K8::Util.parse_query_string("x[]=123&x[]=456")
        ok {d} == {"x[]"=>["123", "456"]}
      end

    end


  end


  topic K8::Request do

    fixture :req do
      K8::Request.new(new_env("GET", "/123"))
    end


    topic '#initialize()' do

      spec "[!yb9k9] sets @env." do
        env = new_env()
        req = K8::Request.new(env)
        ok {req.env}.same?(env)
      end

      spec "[!yo22o] sets @method as Symbol value." do
        req1 = K8::Request.new(new_env("GET"))
        ok {req1.method} == :GET
        req2 = K8::Request.new(new_env("POST"))
        ok {req2.method} == :POST
      end

      spec "[!twgmi] sets @path." do
        req1 = K8::Request.new(new_env("GET", "/123"))
        ok {req1.path} == "/123"
      end

    end


  end


  topic K8::Response do
  end


  topic 'K8::REQUEST=' do

    spec "[!7uqb4] changes default request class." do
      original = K8::REQUEST
      begin
        K8.REQUEST = Array
        ok {K8::REQUEST} == Array
      ensure
        K8.REQUEST = original
      end
    end

  end


  topic 'K8::RESPONSE=' do

    spec "[!c1bd0] changes default response class." do
      original = K8::RESPONSE
      begin
        K8.RESPONSE = Hash
        ok {K8::RESPONSE} == Hash
      ensure
        K8.RESPONSE = original
      end
    end

  end


  topic K8::BaseAction do

    fixture :action do
      env  = new_env("GET", "/books")
      TestBaseAction.new(K8::Request.new(env), K8::Response.new())
    end


    topic '#initialize()' do

      spec "[!uotpb] accepts request and response objects." do
        env    = new_env("GET", "/books")
        req    = K8::Request.new(env)
        resp   = K8::Response.new()
        action = K8::BaseAction.new(req, resp)
        ok {action.instance_variable_get('@req')}.same?(req)
        ok {action.instance_variable_get('@resp')}.same?(resp)
      end

    end


    topic '#handle_action()' do

      spec "[!ddgx3] invokes action method with urlpath params." do
        |action|
        ok {action.handle_action(:do_show, [123])} == "<show:123>"
      end

      spec "[!aqa4e] returns content." do
        |action|
        ok {action.handle_action(:do_index, [])} == "<index>"
        ok {action._called[1]} == ["handle_content", ["<index>"]]
      end

      spec "[!5jnx6] calls '#before_action()' before handling request." do
        |action|
        action.handle_action(:do_index, [])
        ok {action._called[0]} == ["before_action", []]
      end

      spec "[!67awf] calls '#after_action()' after handling request." do
        |action|
        action.handle_action(:do_index, [])
        ok {action._called[-1]} == ["after_action", [nil]]
      end

      spec "[!alpka] calls '#after_action()' even when error raised." do
        |action|
        pr = proc { action.handle_action(:do_create, []) }
        ok {pr}.raise?(ZeroDivisionError)
        ok {action._called[-1]} == ["after_action", [pr.exception]]
      end

    end

  end


  topic K8::Action do

    fixture :action_obj do
      env = new_env("GET", "/")
      BooksAction.new(K8::Request.new(env), K8::Response.new())
    end


    topic '#before_action()' do
    end


    topic '#after_action()' do

      spec "[!qsz2z] raises ContentTypeRequiredError when content type is not set." do
        |action_obj|
        action_obj.instance_exec(self) do |_|
          _.ok {@resp.headers.key?('Content-Type')} == false
          pr = proc { after_action(nil) }
          _.ok {pr}.raise?(K8::ContentTypeRequiredError)
        end
      end

    end


    topic '#handle_content()' do

      case_when "[!jhnzu] when content is nil..." do

        spec "[!42fxs] sets content length as 0." do
          |action_obj|
          action_obj.instance_exec(self) do |_|
            handle_content(nil)
            _.ok {@resp.headers['Content-Length']} == "0"
          end
        end

        spec "[!zcodm] sets content type as octet-stream when not set." do
          |action_obj|
          action_obj.instance_exec(self) do |_|
            handle_content(nil)
            _.ok {@resp.headers['Content-Type']} == "application/octet-stream"
          end
        end

        spec "[!sfwfz] returns ['']." do
          |action_obj|
          action_obj.instance_exec(self) do |_|
            _.ok {handle_content(nil)} == ['']
          end
        end

      end

      case_when "[!lkxua] when content is a hash object..." do

        spec "[!9aaxl] converts hash object into JSON string." do
          |action_obj|
          action_obj.instance_exec(self) do |_|
            _.ok {handle_content({"a"=>nil})} == ['{"a":null}']
          end
        end

        spec "[!c7nj7] sets content length." do
          |action_obj|
          action_obj.instance_exec(self) do |_|
            handle_content({"a"=>nil})
            _.ok {'{"a":null}'.bytesize} == 10
            _.ok {@resp.headers['Content-Length']} == "10"
          end
        end

        spec "[!j0c1d] sets content type as 'application/json' when not set." do
          |action_obj|
          action_obj.instance_exec(self) do |_|
            handle_content({"a"=>nil})
            _.ok {@resp.headers['Content-Type']} == "application/json"
          end
        end

        spec "[!gw05f] returns array of JSON string." do
          |action_obj|
          action_obj.instance_exec(self) do |_|
            _.ok {handle_content({"a"=>nil})} == ['{"a":null}']
          end
        end

      end

      case_when "[!p6p99] when content is a string..." do

        spec "[!1ejgh] sets content length." do
          |action_obj|
          action_obj.instance_exec(self) do |_|
            handle_content("abc")
            _.ok {@resp.headers['Content-Length']} == "3"
          end
        end

        spec "[!uslm5] sets content type according to content when not set." do
          |action_obj|
          action_obj.instance_exec(self) do |_|
            handle_content("<html>")
            _.ok {@resp.headers['Content-Type']} == "text/html; charset=utf-8"
            #
            @resp.headers['Content-Type'] = nil
            handle_content('{"a":1}')
            _.ok {@resp.headers['Content-Type']} == "application/json"
          end
        end

        spec "[!79v6x] returns array of string." do
          |action_obj|
          action_obj.instance_exec(self) do |_|
            _.ok {handle_content("<html>")} == ["<html>"]
          end
        end

      end

      case_when "[!s7eix] when content is an Enumerable object..." do

        spec "[!md2go] just returns content." do
          |action_obj|
          action_obj.instance_exec(self) do |_|
            arr = ["A", "B", "C"]
            _.ok {handle_content(arr)}.same?(arr)
          end
        end

        spec "[!ab3vr] neither content length nor content type are not set." do
          |action_obj|
          action_obj.instance_exec(self) do |_|
            handle_content(["A", "B", "C"])
            _.ok {@resp.headers['Content-Length']} == nil
            _.ok {@resp.headers['Content-Type']}   == nil
          end
        end

      end

      case_when "[!apwh4] else..." do

        spec "[!wmgnr] raises K8::UnknownContentError." do
          |action_obj|
          action_obj.instance_exec(self) do |_|
            pr1 = proc { handle_content(123) }
            _.ok {pr1}.raise?(K8::UnknownContentError)
            pr2 = proc { handle_content(true) }
            _.ok {pr2}.raise?(K8::UnknownContentError)
          end
        end

      end

    end

  end


  topic K8::ActionMappingHelper do

    fixture :mapping do
      cls = Class.new do
        include K8::ActionMappingHelper
      end
      cls.new
    end


    topic 'default_pattern_of_urlpath_parameter()' do

      spec "[!hcnyx] returns '\d+' when name is 'id' or ends with '_id'." do
        |mapping|
        _ = self
        mapping.instance_eval do
          _.ok {default_pattern_of_urlpath_parameter("id")}      == '\d+'
          _.ok {default_pattern_of_urlpath_parameter("book_id")} == '\d+'
        end
      end

      spec "[!gada5] returns '\d\d\d\d-\d\d-\d\d' when name is 'date' or ends with '_date'." do
        |mapping|
        _ = self
        mapping.instance_eval do
          _.ok {default_pattern_of_urlpath_parameter("date")}     == '\d\d\d\d-\d\d-\d\d'
          _.ok {default_pattern_of_urlpath_parameter("end_date")} == '\d\d\d\d-\d\d-\d\d'
        end
      end

      spec "[!adj99] returns '[^/]*?' when other name." do
        |mapping|
        _ = self
        mapping.instance_eval do
          _.ok {default_pattern_of_urlpath_parameter("id_")}   == '[^/]*?'
          _.ok {default_pattern_of_urlpath_parameter("date_")} == '[^/]*?'
        end
      end

    end


    topic 'convert_urlpath_param_value()' do

      spec "[!67ztb] returns Integer value when name is 'id' or ends with '_id'." do
        |mapping|
        mapping.instance_exec(self) do |_|
          _.ok {convert_urlpath_param_value("id", "123")}        == 123
          _.ok {convert_urlpath_param_value("book_id", "0123")}  == 123
        end
      end

      spec "[!0htit] returns Date value when name is 'date' or ends with '_date'." do
        |mapping|
        mapping.instance_exec(self) do |_|
          _.ok {convert_urlpath_param_value("date", "2000-12-31")} == Date.new(2000, 12, 31)
          _.ok {convert_urlpath_param_value("end_date", "2000-01-31")} == Date.new(2000, 1, 31)
        end
      end

      spec "[!2rlse] raises HTTP 404 error when invalid date (such as 2000-02-30)." do
        |mapping|
        mapping.instance_exec(self) do |_|
          pr = proc { convert_urlpath_param_value("date", "2000-02-30") }
          _.ok {pr}.raise?(K8::HttpException, "2000-02-30: invalid date.")
          _.ok {pr.exception.status_code} == 404
        end
      end

      spec "[!y0c2r] returns String value when other name." do
        |mapping|
        mapping.instance_exec(self) do |_|
          _.ok {convert_urlpath_param_value("id_", "123")} == "123"
          _.ok {convert_urlpath_param_value("date_", "2000-12-31")} == "2000-12-31"
        end
      end

    end


  end


  topic K8::ActionMethodMapping do

    fixture :mapping do
      mapping = K8::ActionMethodMapping.new
      mapping.map '/',         :GET=>:do_index, :POST=>:do_create
      mapping.map '/{id:\d+}', :GET=>:do_show, :PUT=>:do_update
      mapping
    end

    fixture :methods1 do
      {:GET=>:do_index, :POST=>:do_create}
    end

    fixture :methods2 do
      {:GET=>:do_show, :PUT=>:do_update}
    end


    topic '#map()' do

      spec "[!s7cs9] maps urlpath and methods." do
        |mapping|
        arr = mapping.instance_variable_get('@mappings')
        ok {arr}.is_a?(Array)
        ok {arr.length} == 2
        ok {arr[0]} == ['/',         {:GET=>:do_index, :POST=>:do_create}]
        ok {arr[1]} == ['/{id:\d+}', {:GET=>:do_show, :PUT=>:do_update}]
      end

      spec "[!o6cxr] returns self." do
        |mapping|
        ok {mapping.map '/new', :GET=>:do_new}.same?(mapping)
      end

    end


    topic '#each_urlpath_and_methods()' do

      spec "[!62y5q] yields each urlpath pattern and action methods." do
        |mapping, methods1, methods2|
        arr = []
        mapping.each_urlpath_and_methods do |urlpath_pat, action_methods|
          arr << [urlpath_pat, action_methods]
        end
        ok {arr} == [
          ['/',         methods1],
          ['/{id:\d+}', methods2],
        ]
      end

    end


  end


  topic K8::ActionClassMapping do

    fixture :mapping do
      K8::ActionClassMapping.new
    end


    topic '#mount()' do

      spec "[!flb11] mounts action class to urlpath." do
        |mapping|
        mapping.mount '/books', BooksAction
        arr = mapping.instance_variable_get('@mappings')
        ok {arr}.is_a?(Array)
        ok {arr.length} == 1
        ok {arr[0]}.is_a?(Array)
        ok {arr[0].length} == 2
        ok {arr[0][0]} == '/books'
        ok {arr[0][1]} == BooksAction
      end

      spec "[!4l8xl] can accept array of pairs of urlpath and action class." do
        |mapping|
        mapping.mount '/api', [
          ['/books', BooksAction],
        ]
        arr = mapping.instance_variable_get('@mappings')
        ok {arr} == [
          ['/api', [
              ['/books', BooksAction],
            ]],
        ]
      end

      spec "[!lvxyx] raises error when not an action class." do
        |mapping|
        pr = proc { mapping.mount '/api', String }
        ok {pr}.raise?(ArgumentError, "mount('/api'): Action class expected but got: String")
      end

      spec "[!w8mee] returns self." do
        |mapping|
        ret = mapping.mount '/books', BooksAction
        ok {ret}.same?(mapping)
      end

      spec "[!dktxq] clears mapping data." do
        |mapping|
        mapping.instance_exec(self) do |_|
          @_mapping_rexp = /_/
          @_mapping_list = []
          @_mapping_dict = {}
          self.mount '/books', BooksAction
          _.ok {@_mapping_rexp} == nil
          _.ok {@_mapping_list} == nil
          _.ok {@_mapping_dict} == nil
        end
      end

    end


    topic '#find()' do

      fixture :methods1 do
        {:GET=>:do_index, :POST=>:do_create}
      end

      fixture :methods2 do
        {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete}
      end


      spec "[!yqedi] returns [action_class, action_methods, urlpath_params] when urlpath matches to action class." do
        |mapping, methods1, methods2|
        mapping.mount '/books', BooksAction
        ok {mapping.find('/books/')}    == [BooksAction, methods1, []]
        ok {mapping.find('/books/')}    == [BooksAction, methods1, []]
        ok {mapping.find('/books/123')} == [BooksAction, methods2, [123]]
        ok {mapping.find('/books/123')} == [BooksAction, methods2, [123]]
      end

      spec "[!d5d5i] can handle nested array of urlpath mapping." do
        |mapping, methods1, methods2|
        mapping.mount '/admin', [
          ['/api', [
              ['/books', BooksAction],
            ]
          ]
        ]
        ok {mapping.find('/admin/api/books/')}    == [BooksAction, methods1, []]
        ok {mapping.find('/admin/api/books/')}    == [BooksAction, methods1, []]
        ok {mapping.find('/admin/api/books/123')} == [BooksAction, methods2, [123]]
        ok {mapping.find('/admin/api/books/123')} == [BooksAction, methods2, [123]]
      end

      spec "[!6qoa3] concatenats all urlpath params in an array." do
        |mapping, methods1, methods2|
        mapping.mount '/stores/{store_id}/books', BooksAction
        tuple = mapping.find('/stores/11/books/22')
        ok {tuple} == [BooksAction, methods2, [11, 22]]
      end

      spec "[!wyb6j] finds next action class when action class found but not matched." do
        |mapping|
        mapping.mount '/books', BooksAction
        mapping.mount '/books/{book_id}', BookCommentsAction
        tuple = mapping.find('/books/123/comments/7')
        ok {tuple} == [BookCommentsAction, {:GET=>:do_comment}, [123, 7]]
      end

      spec "[!hbjar] finds next action recursively class when found but not matched." do
        |mapping|
        mapping.mount '/api', [
          ['/books', BooksAction],
        ]
        mapping.mount '/api', [
          ['/books/{book_id}', BookCommentsAction],
        ]
        tuple = mapping.find('/api/books/123/comments/7')
        ok {tuple} == [BookCommentsAction, {:GET=>:do_comment}, [123, 7]]
      end

      spec "[!1ud98] returns nil when urlpath not found." do
        |mapping|
        mapping.mount '/books', BooksAction
        tuple = mapping.find('/xxx')
        ok {tuple} == nil
        tuple = mapping.find('/books/index.html')
        ok {tuple} == nil
      end

      spec "[!04n9f] finds cache data at first." do
        |mapping, methods1|
        mapping.instance_exec(self) do |_|
          @_mapping_rexp = /\//   # dummy
          _.ok {@_mapping_dict} == nil
          @_mapping_dict = {'/BOOKS' => [BooksAction, methods1]}
          _.ok {find('/BOOKS')} != nil
          _.ok {@_mapping_dict} == {'/BOOKS'=>[BooksAction, methods1]}
        end
      end

    end


    topic '#each_mapping()' do

      spec "[!joje0] yields each full urlpath pattern, action clas and action methods." do
        |mapping|
        mapping.mount '/api', [
          ['/books', BooksAction],
        ]
        arr = []
        mapping.each_mapping do |*args|
          arr << args
        end
        ok {arr} == [
          ['/api/books/',      BooksAction, {:GET=>:do_index, :POST=>:do_create}],
          ['/api/books/new',   BooksAction, {:GET=>:do_new}],
          ['/api/books/{id}',  BooksAction, {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete}],
          ['/api/books/{id}/edit', BooksAction, {:GET=>:do_edit}]
        ]
      end

    end


    topic '#make_mapping_data()' do

      fixture :simple_mapping do
        mapping = K8::ActionClassMapping.new
        mapping.mount '/books', BooksAction
        mapping.__send__(:make_mapping_data)
        mapping
      end

      fixture :complex_mapping do
        mapping = K8::ActionClassMapping.new
        mapping.mount '/api', [
          ['/books',      BooksAction],
          ['/books/{id}', BookCommentsAction],
        ]
        mapping.mount '/admin', [
          ['/books',      AdminBooksAction],
        ]
        mapping.__send__(:make_mapping_data)
        mapping
      end

      spec "[!3aspo] compiles urlpath patterns into a Regexp object." do
        |simple_mapping, complex_mapping|
        rexp = simple_mapping.instance_variable_get('@_mapping_rexp')
        ok {rexp} == Regexp.compile('
          \A
          (?:
            /books(?:/\d+(\z)|/\d+/edit(\z))
          )
        '.gsub(/\s+/, ''))
        #
        rexp = complex_mapping.instance_variable_get('@_mapping_rexp')
        ok {rexp} == Regexp.compile('
          \A
          (?:
            /api
              (?:
                /books(?:/\d+(\z)|/\d+/edit(\z))
              | /books/\d+(?:/comments(\z)|/comments/\d+(\z))
              )
          | /admin
              (?:
                /books(?:/\d+(\z)|/\d+/edit(\z))
              )
          )
        '.gsub(/\s+/, ''))
      end

      spec "[!7hkq6] collects fixed urlpath patterns as Hash object." do
        |simple_mapping, complex_mapping|
        dict = simple_mapping.instance_variable_get('@_mapping_dict')
        ok {dict} == {
          "/books/"   =>[BooksAction, {:GET=>:do_index, :POST=>:do_create}],
          "/books/new"=>[BooksAction, {:GET=>:do_new}],
        }
        #
        dict = complex_mapping.instance_variable_get('@_mapping_dict')
        ok {dict} == {
          "/api/books/"     =>[BooksAction,      {:GET=>:do_index, :POST=>:do_create}],
          "/api/books/new"  =>[BooksAction,      {:GET=>:do_new}],
          "/admin/books/"   =>[AdminBooksAction, {:GET=>:do_index, :POST=>:do_create}],
          "/admin/books/new"=>[AdminBooksAction, {:GET=>:do_new}],
        }
      end

      spec "[!cny8a] collects variable urlpath patterns as Array object." do
        |simple_mapping, complex_mapping|
        list = simple_mapping.instance_variable_get('@_mapping_list')
        ok {list} == [
          [
            %r`\A/books/(\d+)\z`,
            ["id"],
            BooksAction,
            {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete},
          ],
          [
            %r`\A/books/(\d+)/edit\z`,
            ["id"],
            BooksAction,
            {:GET=>:do_edit},
          ],
        ]
        #
        list = complex_mapping.instance_variable_get('@_mapping_list')
        ok {list} == [
          [
            %r`\A/api/books/(\d+)\z`,
            ["id"],
            BooksAction,
            {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete},
          ],
          [
            %r`\A/api/books/(\d+)/edit\z`,
            ["id"],
            BooksAction,
            {:GET=>:do_edit},
          ],
          [
            %r`\A/api/books/(\d+)/comments\z`,
            ["id"],
            BookCommentsAction,
            {:GET=>:do_comments},
          ],
          [
            %r`\A/api/books/(\d+)/comments/(\d+)\z`,
            ["id", "comment_id"],
            BookCommentsAction,
            {:GET=>:do_comment},
          ],
          [
            %r`\A/admin/books/(\d+)\z`,
            ["id"],
            AdminBooksAction,
            {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete},
          ],
          [
            %r`\A/admin/books/(\d+)/edit\z`,
            ["id"],
            AdminBooksAction,
            {:GET=>:do_edit},
          ],
        ]
      end

    end


    topic '#_compile()' do

      spec "[!izsbp] compiles urlpath pattern into regexp string and param names." do
        |mapping|
        _ = self
        mapping.instance_eval do
          ret = _compile('/', '\A', '\z', true)
          _.ok {ret} == ['\A/\z', []]
          ret = _compile('/books', '\A', '\z', true)
          _.ok {ret} == ['\A/books\z', []]
          ret = _compile('/books/{id:\d*}', '\A', '\z', true)
          _.ok {ret} == ['\A/books/(\d*)\z', ["id"]]
          ret = _compile('/books/{id}/authors/{name}', '\A', '\z', true)
          _.ok {ret} == ['\A/books/(\d+)/authors/([^/]*?)\z', ["id", "name"]]
        end
      end

      spec "[!2zil2] don't use grouping when 4th argument is false." do
        |mapping|
        _ = self
        mapping.instance_eval do
          ret = _compile('/books/{id:\d*}', '\A', '\z', true)
          _.ok {ret} == ['\A/books/(\d*)\z', ["id"]]
          ret = _compile('/books/{id}/authors/{name}', '\A', '\z', true)
          _.ok {ret} == ['\A/books/(\d+)/authors/([^/]*?)\z', ["id", "name"]]
          #
          ret = _compile('/books/{id:\d*}', '\A', '\z', false)
          _.ok {ret} == ['\A/books/\d*\z', ["id"]]
          ret = _compile('/books/{id}/authors/{name}', '\A', '\z', false)
          _.ok {ret} == ['\A/books/\d+/authors/[^/]*?\z', ["id", "name"]]
        end
      end

    end


  end


  topic K8::RackApplication do

    fixture :app do
      app = K8::RackApplication.new
      app.mount '/api', [
        ['/books', BooksAction],
      ]
      app
    end


    topic '#call()' do

      spec "[!uvmxe] takes env object." do
        |app|
        env = new_env("GET", "/api/books/")
        pr = proc {app.call(env)}
        ok {pr}.NOT.raise?(Exception)
      end

      spec "[!gpe4g] returns status, headers and content." do
        |app|
        env = new_env("GET", "/api/books/")
        ret = app.call(env)
        ok {ret}.is_a?(Array)
        status, headers, body = ret
        ok {status}  == 200
        ok {headers} == {
          "Content-Type"=>"text/html; charset=utf-8",
          "Content-Length"=>"7",
        }
        ok {body} == ["<index>"]
      end

    end


    topic '#handle_request()' do

      spec "[!0fgbd] finds action class and invokes action method with urlpath params." do
        |app|
        env = new_env("GET", "/api/books/123")
        app.instance_exec(self) do |_|
          tuple = handle_request(K8::Request.new(env), K8::Response.new)
          _.ok {tuple}.is_a?(Array)
          status, headers, body = tuple
          _.ok {status}  == 200
          _.ok {body}    == ["<show:123(Fixnum)>"]
          _.ok {headers} == {
            "Content-Length" => "18",
            "Content-Type"   => "text/html; charset=utf-8",
          }
        end
      end

      spec "[!l6kmc] uses 'GET' method to find action when request method is 'HEAD'." do
        |app|
        env = new_env("HEAD", "/api/books/123")
        app.instance_exec(self) do |_|
          tuple = handle_request(K8::Request.new(env), K8::Response.new)
          status, headers, body = tuple
          _.ok {status}  == 200
          _.ok {body}    == [""]
          _.ok {headers} == {
            "Content-Length" => "18",
            "Content-Type"   => "text/html; charset=utf-8",
          }
        end
      end

      spec "[!9wp9z] returns empty body when request method is HEAD." do
        |app|
        env = new_env("HEAD", "/api/books/123")
        app.instance_exec(self) do |_|
          tuple = handle_request(K8::Request.new(env), K8::Response.new)
          status, headers, body = tuple
          _.ok {body} == [""]
        end
      end

      spec "[!rz13i] returns HTTP 404 when urlpath not found." do
        |app|
        env = new_env("GET", "/api/book/comments")
        app.instance_exec(self) do |_|
          tuple = handle_request(K8::Request.new(env), K8::Response.new)
          status, headers, body = tuple
          _.ok {status}  == 404
          _.ok {body}    == ["<div>\n<h2>404 Not Found</h2>\n<p></p>\n</div>\n"]
          _.ok {headers} == {
            "Content-Length" => "44",
            "Content-Type"   => "text/html;charset=utf-8",
          }
        end
      end

      spec "[!rv3cf] returns HTTP 405 when urlpath found but request method not allowed." do
        |app|
        env = new_env("POST", "/api/books/123")
        app.instance_exec(self) do |_|
          tuple = handle_request(K8::Request.new(env), K8::Response.new)
          status, headers, body = tuple
          _.ok {status}  == 405
          _.ok {body}    == ["<div>\n<h2>405 Method Not Allowed</h2>\n<p></p>\n</div>\n"]
          _.ok {headers} == {
            "Content-Length" => "53",
            "Content-Type"   => "text/html;charset=utf-8",
          }
        end
      end


    end


  end


end


if __FILE__ == $0
  Oktest::main()
end
