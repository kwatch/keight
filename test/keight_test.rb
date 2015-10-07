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


  topic K8::DefaultPatterns do


    topic '#register()' do

      spec "[!yfsom] registers urlpath param name, default pattern and converter block." do
        K8::DefaultPatterns.new.instance_exec(self) do |_|
          _.ok {@patterns.length} == 0
          register(/_id\z/, '\d+') {|x| x.to_i }
          _.ok {@patterns.length} == 1
          _.ok {@patterns[0][0]} == /_id\z/
          _.ok {@patterns[0][1]} == '\d+'
          _.ok {@patterns[0][2]}.is_a?(Proc)
          _.ok {@patterns[0][2].call("123")} == 123
        end
      end

    end


    topic '#unregister()' do

      spec "[!3gplv] deletes matched record." do
        K8::DefaultPatterns.new.instance_exec(self) do |_|
          register("id",    '\d+') {|x| x.to_i }
          register(/_id\z/, '\d+') {|x| x.to_i }
          _.ok {@patterns.length} == 2
          unregister(/_id\z/)
          _.ok {@patterns.length} == 1
          _.ok {@patterns[0][0]} == "id"
        end
      end

    end


    topic '#lookup()' do

      spec "[!dvbqx] returns default pattern string and converter proc when matched." do
        K8::DefaultPatterns.new.instance_exec(self) do |_|
          register("id",    '\d+') {|x| x.to_i }
          register(/_id\z/, '\d+') {|x| x.to_i }
          _.ok {lookup("id")}.is_a?(Array).length(2)
          _.ok {lookup("id")[0]} == '\d+'
          _.ok {lookup("id")[1].call("123")} == 123
          _.ok {lookup("book_id")[0]} == '\d+'
          _.ok {lookup("book_id")[1]}.is_a?(Proc)
          _.ok {lookup("book_id")[1].call("123")} == 123
        end
      end

      spec "[!6hblo] returns '[^/]*?' and nil as default pattern and converter proc when nothing matched." do
        K8::DefaultPatterns.new.instance_exec(self) do |_|
          register("id",    '\d+') {|x| x.to_i }
          register(/_id\z/, '\d+') {|x| x.to_i }
          _.ok {lookup("code")}.is_a?(Array).length(2)
          _.ok {lookup("code")[0]} == '[^/]+?'
          _.ok {lookup("code")[1]} == nil
        end
      end

    end

  end


  topic K8::DEFAULT_PATTERNS do

    fixture :default_patterns do
      K8::DEFAULT_PATTERNS
    end

    spec "[!6hh7o] default pattern of urlpath param name 'id' or 'xxx_id' is '\d+'." do
      |default_patterns|
      pat, proc_ = default_patterns.lookup('id')
      ok {pat} == '\d+'
      ok {proc_.call("123")} == 123
      #
      pat, proc_ = default_patterns.lookup('book_id')
      ok {pat} == '\d+'
      ok {proc_.call("123")} == 123
    end

    spec "[!jisj0] default pattern of urlpath param name 'date' or 'xxx_date' is '\\d\\d\\d\\d-\\d\\d-\\d\\d'." do
      |default_patterns|
      pat, proc_ = default_patterns.lookup('date')
      ok {pat} == '\d\d\d\d-\d\d-\d\d'
      ok {proc_.call("2014-12-24")} == Date.new(2014, 12, 24)
      #
      pat, proc_ = default_patterns.lookup('birth_date')
      ok {pat} == '\d\d\d\d-\d\d-\d\d'
      ok {proc_.call("2015-02-14")} == Date.new(2015, 2, 14)
    end

    spec "[!yv6i6] raises HTTP 404 error when invalid date (such as 2000-02-30)." do
      |default_patterns|
      pat, proc_ = default_patterns.lookup('date')
      pr = proc { proc_.call("2014-02-30") }
      ok {pr}.raise?(K8::HttpException, "2014-02-30: invalid date.")
      ok {pr.exception.status_code} == 404
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

    fixture :proc_obj1 do
      _, proc_obj = K8::DEFAULT_PATTERNS.lookup('id')
      proc_obj
    end

    fixture :proc_obj2 do
      _, proc_obj = K8::DEFAULT_PATTERNS.lookup('book_id')
      proc_obj
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

    end


    topic '#traverse()' do

      spec "[!ds0fp] yields with event (:enter, :map or :exit)." do
        mapping = K8::ActionClassMapping.new
        mapping.mount '/api', [
          ['/books', BooksAction],
          ['/books/{book_id}/comments', BookCommentsAction],
        ]
        mapping.mount '/admin', [
          ['/books', AdminBooksAction],
        ]
        #
        arr = []
        mapping.traverse do |*args|
          arr << args
        end
        ok {arr[0]} == [:enter, "", "/api", [["/books", BooksAction], ["/books/{book_id}/comments", BookCommentsAction]], nil]
        ok {arr[1]} == [:enter, "/api", "/books", BooksAction, nil]
        ok {arr[2]} == [:map,   "/api/books", "/", BooksAction, {:GET=>:do_index, :POST=>:do_create}]
        ok {arr[3]} == [:map,   "/api/books", "/new", BooksAction, {:GET=>:do_new}]
        ok {arr[4]} == [:map,   "/api/books", "/{id}", BooksAction, {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete}]
        ok {arr[5]}  == [:map,   "/api/books", "/{id}/edit", BooksAction, {:GET=>:do_edit}]
        ok {arr[6]}  == [:exit,  "/api", "/books", BooksAction, nil]
        ok {arr[7]}  == [:enter, "/api", "/books/{book_id}/comments", BookCommentsAction, nil]
        ok {arr[8]}  == [:map,   "/api/books/{book_id}/comments", "/comments", BookCommentsAction, {:GET=>:do_comments}]
        ok {arr[9]}  == [:map,   "/api/books/{book_id}/comments", "/comments/{comment_id}", BookCommentsAction, {:GET=>:do_comment}]
        ok {arr[10]} == [:exit,  "/api", "/books/{book_id}/comments", BookCommentsAction, nil]
        ok {arr[11]} == [:exit,  "", "/api", [["/books", BooksAction], ["/books/{book_id}/comments", BookCommentsAction]], nil]
        ok {arr[12]} == [:enter, "", "/admin", [["/books", AdminBooksAction]], nil]
        ok {arr[13]} == [:enter, "/admin", "/books", AdminBooksAction, nil]
        ok {arr[14]} == [:map,   "/admin/books", "/", AdminBooksAction, {:GET=>:do_index, :POST=>:do_create}]
        ok {arr[15]} == [:map,   "/admin/books", "/new", AdminBooksAction, {:GET=>:do_new}]
        ok {arr[16]} == [:map,   "/admin/books", "/{id}", AdminBooksAction, {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete}]
        ok {arr[17]} == [:map,   "/admin/books", "/{id}/edit", AdminBooksAction, {:GET=>:do_edit}]
        ok {arr[18]} == [:exit,  "/admin", "/books", AdminBooksAction, nil]
        ok {arr[19]} == [:exit,  "", "/admin", [["/books", AdminBooksAction]], nil]
        ok {arr[20]} == nil
      end

    end


  end


  topic K8::ActionRouter do

    fixture :router do
      mapping = K8::ActionClassMapping.new
      mapping.mount '/api', [
        ['/books', BooksAction],
        ['/books/{book_id}', BookCommentsAction],
      ]
      mapping.mount '/admin', [
        ['/books', AdminBooksAction],
      ]
      router = K8::ActionRouter.new(mapping, K8::DEFAULT_PATTERNS)
      router
    end

    fixture :proc_obj1 do
      _, proc_obj = K8::DEFAULT_PATTERNS.lookup("id")
      proc_obj
    end

    fixture :proc_obj2 do
      _, proc_obj = K8::DEFAULT_PATTERNS.lookup("xxx_id")
      proc_obj
    end


    topic '#initialize()' do

      spec "[!dnu4q] calls '#_construct()'." do
        |router|
        ok {router.instance_variable_get('@rexp')} != nil
        ok {router.instance_variable_get('@list')} != nil
        ok {router.instance_variable_get('@dict')} != nil
      end

    end


    topic '#_compile()' do

      spec "[!izsbp] compiles urlpath pattern into regexp string and param names." do
        |router, proc_obj1|
        router.instance_exec(self) do |_|
          ret = _compile('/', '\A', '\z', true)
          _.ok {ret} == ['\A/\z', [], []]
          ret = _compile('/books', '\A', '\z', true)
          _.ok {ret} == ['\A/books\z', [], []]
          ret = _compile('/books/{id:\d*}', '\A', '\z', true)
          _.ok {ret} == ['\A/books/(\d*)\z', ["id"], [nil]]
          ret = _compile('/books/{id}/authors/{name}', '\A', '\z', true)
          _.ok {ret} == ['\A/books/(\d+)/authors/([^/]+?)\z', ["id", "name"], [proc_obj1, nil]]
        end
      end

      spec "[!olps9] allows '{}' in regular expression." do
        |router|
        router.instance_exec(self) do |_|
          ret = _compile('/log/{date:\d{4}-\d{2}-\d{2}}', '', '', true)
          _.ok {ret} == ['/log/(\d{4}-\d{2}-\d{2})', ["date"], [nil]]
        end
      end

      spec "[!vey08] uses grouping when 4th argument is true." do
        |router, proc_obj1|
        router.instance_exec(self) do |_|
          ret = _compile('/books/{id:\d*}', '\A', '\z', true)
          _.ok {ret} == ['\A/books/(\d*)\z', ["id"], [nil]]
          ret = _compile('/books/{id}/authors/{name}', '\A', '\z', true)
          _.ok {ret} == ['\A/books/(\d+)/authors/([^/]+?)\z', ["id", "name"], [proc_obj1, nil]]
        end
      end

      spec "[!2zil2] don't use grouping when 4th argument is false." do
        |router, proc_obj1|
        router.instance_exec(self) do |_|
          ret = _compile('/books/{id:\d*}', '\A', '\z', false)
          _.ok {ret} == ['\A/books/\d*\z', ["id"], [nil]]
          ret = _compile('/books/{id}/authors/{name}', '\A', '\z', false)
          _.ok {ret} == ['\A/books/\d+/authors/[^/]+?\z', ["id", "name"], [proc_obj1, nil]]
        end
      end

      spec %q"[!rda92] ex: '/{id:\d+}' -> '/(\d+)'" do
        |router|
        router.instance_exec(self) do |_|
          ret = _compile('/api/{ver:\d+}', '', '', true)
          _.ok {ret} == ['/api/(\d+)', ["ver"], [nil]]
        end
      end

      spec %q"[!jyz2g] ex: '/{:\d+}'   -> '/\d+'" do
        |router|
        router.instance_exec(self) do |_|
          ret = _compile('/api/{:\d+}', '', '', true)
          _.ok {ret} == ['/api/\d+', [], []]
        end
      end

      spec %q"[!hy3y5] ex: '/{:xx|yy}' -> '/(?:xx|yy)'" do
        |router|
        router.instance_exec(self) do |_|
          ret = _compile('/api/{:2014|2015}', '', '', true)
          _.ok {ret} == ['/api/(?:2014|2015)', [], []]
        end
      end

      spec %q"[!gunsm] ex: '/{id:xx|yy}' -> '/(xx|yy)'" do
        |router|
        router.instance_exec(self) do |_|
          ret = _compile('/api/{year:2014|2015}', '', '', true)
          _.ok {ret} == ['/api/(2014|2015)', ["year"], [nil]]
        end
      end

    end


    topic '#_construct()' do

      spec "[!956fi] builds regexp object for variable urlpaths (= containing urlpath params)." do
        |router|
        rexp = router.instance_variable_get('@rexp')
        ok {rexp}.is_a?(Regexp)
        ok {rexp.source} == '
            \A
            (?:
                /api
                    (?:
                        /books
                            (?: /\d+(\z) | /\d+/edit(\z) )
                    |
                        /books/\d+
                            (?: /comments(\z) | /comments/\d+(\z) )
                    )
            |
                /admin
                    (?:
                        /books
                            (?: /\d+(\z) | /\d+/edit(\z) )
                    )
            )
        '.gsub(/\s+/, '')
      end

      spec "[!6tgj5] builds dict of fixed urlpaths (= no urlpath params)." do
        |router|
        dict = router.instance_variable_get('@dict')
        ok {dict} == {
          '/api/books/'      => [BooksAction,      {:GET=>:do_index, :POST=>:do_create}],
          '/api/books/new'   => [BooksAction,      {:GET=>:do_new}],
          '/admin/books/'    => [AdminBooksAction, {:GET=>:do_index, :POST=>:do_create}],
          '/admin/books/new' => [AdminBooksAction, {:GET=>:do_new}],
        }
      end

      spec "[!sl9em] builds list of variable urlpaths (= containing urlpath params)." do
        |router, proc_obj1, proc_obj2|
        list = router.instance_variable_get('@list')
        ok {list}.is_a?(Array)
        ok {list.length} == 6
        ok {list[0]} == [
          /\A\/api\/books\/(\d+)\z/,
          ["id"], [proc_obj1],
          BooksAction,
          {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete},
        ]
        ok {list[1]} == [
          /\A\/api\/books\/(\d+)\/edit\z/,
          ["id"], [proc_obj1],
          BooksAction,
          {:GET=>:do_edit},
        ]
        ok {list[2]} == [
          /\A\/api\/books\/(\d+)\/comments\z/,
          ["book_id"], [proc_obj2],
          BookCommentsAction,
          {:GET=>:do_comments},
        ]
        ok {list[3]} == [
          /\A\/api\/books\/(\d+)\/comments\/(\d+)\z/,
          ["book_id", "comment_id"], [proc_obj2, proc_obj2],
          BookCommentsAction,
          {:GET=>:do_comment},
        ]
        ok {list[4]} == [
          /\A\/admin\/books\/(\d+)\z/,
          ["id"], [proc_obj1],
          AdminBooksAction,
          {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete},
        ]
        ok {list[5]} == [
          /\A\/admin\/books\/(\d+)\/edit\z/,
          ["id"], [proc_obj1],
          AdminBooksAction,
          {:GET=>:do_edit},
        ]
        ok {list[6]} == nil
      end

    end


    topic '#find()' do

      spec "[!ndktw] returns action class, action methods, urlpath names and values." do
        |router|
        ok {router.find('/api/books/')} == [
          BooksAction, {:GET=>:do_index, :POST=>:do_create}, [], [],
        ]
        ok {router.find('/api/books/123')} == [
          BooksAction, {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete}, ["id"], [123],
        ]
      end

      spec "[!p18w0] urlpath params are empty when matched to fixed urlpath pattern." do
        |router|
        ok {router.find('/admin/books/')} == [
          AdminBooksAction, {:GET=>:do_index, :POST=>:do_create}, [], [],
        ]
      end

      spec "[!t6yk0] urlpath params are not empty when matched to variable urlpath apttern." do
        |router|
        ok {router.find('/admin/books/123')} == [
          AdminBooksAction, {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete}, ["id"], [123],
        ]
        ok {router.find('/api/books/123/comments/999')} == [
          BookCommentsAction, {:GET=>:do_comment}, ["book_id", "comment_id"], [123, 999],
        ]
      end

      spec "[!0o3fe] converts urlpath param values according to default patterns." do
        |router|
        ok {router.find('/api/books/123')[-1]} == [123]
        ok {router.find('/api/books/123/comments/999')[-1]} == [123, 999]
      end

      spec "[!ps5jm] returns nil when not matched to any urlpath patterns." do
        |router|
        ok {router.find('/admin/authors')} == nil
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


    topic '#mount()' do

      spec "[!fm8mh] clears router object." do
        |app|
        app.instance_exec(self) do |_|
          @router = true
          mount '/admin', AdminBooksAction
          _.ok {@router} == nil
        end
      end

    end


    topic '#find()' do

      spec "[!vnxoo] creates router object from action class mapping if router is nil." do
        |app|
        app.instance_exec(self) do |_|
          _.ok {@router} == nil
          find('/')
          _.ok {@router} != nil
          _.ok {@router}.is_a?(K8::ActionRouter)
        end
      end

      spec "[!o0rnr] returns action class, action methods, urlpath names and values." do
        |app|
        ret = app.find('/api/books/')
        ok {ret} == [BooksAction, {:GET=>:do_index, :POST=>:do_create}, [], []]
        ret = app.find('/api/books/123')
        ok {ret} == [BooksAction, {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete}, ["id"], [123]]
      end

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


    topic '#each_mapping()' do

      spec "[!cgjyv] yields full urlpath pattern, action class and action methods." do
        |app|
        arr = []
        app.each_mapping do |*args|
          arr << args
        end
        ok {arr} == [
          ["/api/books/", BooksAction, {:GET=>:do_index, :POST=>:do_create}],
          ["/api/books/new", BooksAction, {:GET=>:do_new}],
          ["/api/books/{id}", BooksAction, {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete}],
          ["/api/books/{id}/edit", BooksAction, {:GET=>:do_edit}],
        ]
      end

    end


    topic '#show_mappings()' do

      spec "[!u1g77] returns all mappings as YAML string." do
        |app|
        ok {app.show_mappings()} == <<'END'
- urlpath: /api/books/
  class:   BooksAction
  methods: {GET: do_index, POST: do_create}

- urlpath: /api/books/new
  class:   BooksAction
  methods: {GET: do_new}

- urlpath: /api/books/{id}
  class:   BooksAction
  methods: {GET: do_show, PUT: do_update, DELETE: do_delete}

- urlpath: /api/books/{id}/edit
  class:   BooksAction
  methods: {GET: do_edit}

END
      end

    end


  end


end


if __FILE__ == $0
  Oktest::main()
end
