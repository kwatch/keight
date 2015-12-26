# -*- coding: utf-8 -*-

$LOAD_PATH << "lib"  unless $LOAD_PATH.include?("lib")
$LOAD_PATH << "test" unless $LOAD_PATH.include?("test")

require 'stringio'

require 'rack/test_app'
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
  def do_new();      "<new>";    end
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
  def do_new(); end
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
  def handle_exception(*args)
    self._called << ["handle_exception", args]
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


class TestExceptionAction < K8::Action

  def do_create
    1/0   #=> ZeroDivisionError
  end

end


Oktest.scope do

  def new_env(meth="GET", path="/", opts={})
    return Rack::TestApp.new_env(meth, path, opts)
  end


  topic K8::Util do


    topic '.escape_html()' do

      spec "[!90jx8] escapes '& < > \" \'' into '&amp; &lt; &gt; &quot; &#39;'." do
        ok {K8::Util.escape_html('& < > " \'')} == '&amp; &lt; &gt; &quot; &#39;'
      end

    end


    topic '.h()' do

      spec "[!649wt] 'h()' is alias of 'escape_html()'" do
        ok {K8::Util.h('& < > " \'')} == '&amp; &lt; &gt; &quot; &#39;'
      end

    end


    topic '.percent_encode()' do

      spec "[!a96jo] encodes string into percent encoding format." do
        ok {K8::Util.percent_encode('[xxx]')} == "%5Bxxx%5D"
      end

    end


    topic '.percent_decode()' do

      spec "[!kl9sk] decodes percent encoded string." do
        ok {K8::Util.percent_decode('%5Bxxx%5D')} == "[xxx]"
      end

    end


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


    topic '.parse_multipart()' do

      fixture :multipart_data do
        data_dir = File.join(File.dirname(__FILE__), "data")
        data = File.open("#{data_dir}/multipart.form", 'rb') {|f| f.read() }
        data
      end

      fixture :boundary do |multipart_data|
        boundary = /\A--(.*)\r\n/.match(multipart_data)[1]
        boundary
      end

      spec "[!mqrei] parses multipart form data." do
        |multipart_data, boundary|
        begin
          data = multipart_data
          data_dir = File.join(File.dirname(__FILE__), "data")
          stdin = StringIO.new(data)
          params, files = K8::Util.parse_multipart(stdin, boundary, data.length)
          ok {params} == {
            'text1'  => "test1",
            'text2'  => "日本語\r\nあいうえお\r\n".force_encoding('binary'),
            'file1'  => "example1.png",
            'file2'  => "example1.jpg",
          }
          #
          upfile1 = files['file1']
          ok {upfile1}.is_a?(K8::UploadedFile)
          ok {upfile1.filename}     == "example1.png"
          ok {upfile1.content_type} == "image/png"
          ok {upfile1.tmp_filepath}.file_exist?
          tmpfile1 = upfile1.tmp_filepath
          ok {File.size(tmpfile1)}  == File.size("#{data_dir}/example1.png")
          ok {File.read(tmpfile1)}  == File.read("#{data_dir}/example1.png")
          #
          upfile2 = files['file2']
          ok {upfile2}.is_a?(K8::UploadedFile)
          ok {upfile2.filename}     == "example1.jpg"
          ok {upfile2.content_type} == "image/jpeg"
          ok {upfile2.tmp_filepath}.file_exist?
          tmpfile2 = upfile2.tmp_filepath
          ok {File.size(tmpfile2)}  == File.size("#{data_dir}/example1.jpg")
          ok {File.read(tmpfile2)}  == File.read("#{data_dir}/example1.jpg")
        ensure
          files.values.each {|x| x.clean() } if files
        end
      end

    end


    topic '.randstr_b64()' do

      spec "[!yq0gv] returns random string, encoded with urlsafe base64." do
        arr = (1..1000).map { K8::Util.randstr_b64() }
        ok {arr.sort.uniq.length} == 1000
        arr.each do |s|
          ok {s} =~ /\A[-\w]+\z/
          ok {s.length} == 27
        end
      end

    end


    topic '.guess_content_type()' do

      spec "[!xw0js] returns content type guessed from filename." do
        ok {K8::Util.guess_content_type("foo.html")} == "text/html"
        ok {K8::Util.guess_content_type("foo.jpg")}  == "image/jpeg"
        ok {K8::Util.guess_content_type("foo.json")} == "application/json"
        ok {K8::Util.guess_content_type("foo.xls")}  == "application/vnd.ms-excel"
      end

      spec "[!dku5c] returns 'application/octet-stream' when failed to guess content type." do
        ok {K8::Util.guess_content_type("foo.rbc")}  == "application/octet-stream"
        ok {K8::Util.guess_content_type("foo")}      == "application/octet-stream"
      end

    end


    topic '#http_utc_time()' do

      spec "[!5k50b] converts Time object into HTTP date format string." do
        require 'time'
        t = Time.new(2015, 2, 3, 4, 5, 6).utc
        ok {K8::Util.http_utc_time(t)} == t.httpdate
        now = Time.now.utc
        ok {K8::Util.http_utc_time(now)} == now.httpdate
      end

      spec "[!3z5lf] raises error when argument is not UTC." do
        t = Time.new(2015, 2, 3, 4, 5, 6)
        pr = proc { K8::Util.http_utc_time(t) }
        ok {pr}.raise?(ArgumentError, /\Ahttp_utc_time\(2015-02-03 04:05:06 [-+]\d{4}\): expected UTC time but got local time.\z/)
      end

    end


  end


  topic K8::UploadedFile do


    topic '#initialize()' do

      spec "[!ityxj] takes filename and content type." do
        x = K8::UploadedFile.new("hom.html", "text/html")
        ok {x.filename} == "hom.html"
        ok {x.content_type} == "text/html"
      end

      spec "[!5c8w6] sets temporary filepath with random string." do
        arr = (1..1000).collect { K8::UploadedFile.new("x", "x").tmp_filepath }
        ok {arr.sort.uniq.length} == 1000
      end

      spec "[!8ezhr] yields with opened temporary file." do
        begin
          s = "homhom"
          x = K8::UploadedFile.new("hom.html", "text/html") {|f| f.write(s) }
          ok {x.tmp_filepath}.file_exist?
          ok {File.open(x.tmp_filepath) {|f| f.read() }} == s
        ensure
          File.unlink(x.tmp_filepath) if File.exist?(x.tmp_filepath)
        end
      end

    end


    topic '#clean()' do

      spec "[!ft454] removes temporary file if exists." do
        begin
          x = K8::UploadedFile.new("hom.html", "text/html") {|f| f.write("hom") }
          ok {x.tmp_filepath}.file_exist?
          x.clean()
          ok {x.tmp_filepath}.NOT.file_exist?
        ensure
          File.unlink(x.tmp_filepath) if File.exist?(x.tmp_filepath)
        end
      end

    end


    topic '#new_filepath()' do

      spec "[!zdkts] use $K8_UPLOAD_DIR environment variable as temporary directory." do
        orig = ENV['K8_UPLOAD_DIR']
        ENV['K8_UPLOAD_DIR'] = "/var/tmp/upload"
        begin
          upfile = K8::UploadedFile.new("hom.txt", "text/plain")
          ok {upfile.__send__(:new_filepath)} =~ /\A\/var\/tmp\/upload\/up\./
        ensure
          ENV['K8_UPLOAD_DIR'] = orig
        end
      end

    end

  end


  topic K8::Request do

    fixture :req do
      K8::Request.new(new_env("GET", "/123"))
    end

    fixture :data_dir do
      File.join(File.dirname(__FILE__), "data")
    end

    fixture :multipart_env do |data_dir|
      input = File.open("#{data_dir}/multipart.form", 'rb') {|f| f.read() }
      boundary = /\A--(.+)\r\n/.match(input)[1]
      cont_type = "multipart/form-data;boundary=#{boundary}"
      env = new_env("POST", "/", input: input, env: {'CONTENT_TYPE'=>cont_type})
      env
    end


    topic '#initialize()' do

      spec "[!yb9k9] sets @env." do
        env = new_env()
        req = K8::Request.new(env)
        ok {req.env}.same?(env)
      end

      spec "[!yo22o] sets @meth as Symbol value." do
        req1 = K8::Request.new(new_env("GET"))
        ok {req1.meth} == :GET
        req2 = K8::Request.new(new_env("POST"))
        ok {req2.meth} == :POST
      end

      spec "[!twgmi] sets @path." do
        req1 = K8::Request.new(new_env("GET", "/123"))
        ok {req1.path} == "/123"
      end

      spec "[!ae8ws] uses SCRIPT_NAME as urlpath when PATH_INFO is not provided." do
        env = new_env("GET", "/123", env: {'SCRIPT_NAME'=>'/index.cgi'})
        env['PATH_INFO'] = ''
        ok {K8::Request.new(env).path} == "/index.cgi"
        env.delete('PATH_INFO')
        ok {K8::Request.new(env).path} == "/index.cgi"
      end

    end


    topic '#header()' do

      spec "[!1z7wj] returns http header value from environment." do
        env = new_env("GET", "/",
                      headers: {'Accept-Encoding'=>'gzip,deflate'},
                      env:     {'HTTP_ACCEPT_LANGUAGE'=>'en,ja'})
        req = K8::Request.new(env)
        ok {req.header('Accept-Encoding')} == 'gzip,deflate'
        ok {req.header('Accept-Language')} == 'en,ja'
      end

    end


    topic '#request_method' do

      spec "[!y8eos] returns env['REQUEST_METHOD'] as string." do
        req = K8::Request.new(new_env(:POST, "/"))
        ok {req.request_method} == "POST"
      end

    end


    topic '#content_type' do

      spec "[!95g9o] returns env['CONTENT_TYPE']." do
        ctype = "text/html"
        req = K8::Request.new(new_env("GET", "/", env: {'CONTENT_TYPE'=>ctype}))
        ok {req.content_type} == ctype
        req = K8::Request.new(new_env("GET", "/", env: {}))
        ok {req.content_type} == nil
      end

    end


    topic '#content_length' do

      spec "[!0wbek] returns env['CONTENT_LENGHT'] as integer." do
        req = K8::Request.new(new_env("GET", "/", env: {'CONTENT_LENGTH'=>'0'}))
        ok {req.content_length} == 0
        req.env.delete('CONTENT_LENGTH')
        ok {req.content_length} == nil
      end

    end


    topic '#xhr?' do

      spec "[!hsgkg] returns true when 'X-Requested-With' header is 'XMLHttpRequest'." do
        env = new_env("GET", "/", headers: {'X-Requested-With'=>'XMLHttpRequest'})
        ok {K8::Request.new(env).xhr?} == true
        env = new_env("GET", "/", headers: {})
        ok {K8::Request.new(env).xhr?} == false
      end

    end


    topic '#client_ip_addr' do

      spec "[!e1uvg] returns 'X-Real-IP' header value if provided." do
        env = new_env("GET", "/",
                      headers: {'X-Real-IP'=>'192.168.1.23'},
                      env: {'REMOTE_ADDR'=>'192.168.0.1'})
        ok {K8::Request.new(env).client_ip_addr} == '192.168.1.23'
      end

      spec "[!qdlyl] returns first item of 'X-Forwarded-For' header if provided." do
        env = new_env("GET", "/",
                      headers: {'X-Forwarded-For'=>'192.168.1.1, 192.168.1.2, 192.168.1.3'},
                      env: {'REMOTE_ADDR'=>'192.168.0.1'})
        ok {K8::Request.new(env).client_ip_addr} == '192.168.1.1'
      end

      spec "[!8nzjh] returns 'REMOTE_ADDR' if neighter 'X-Real-IP' nor 'X-Forwarded-For' provided." do
        env = new_env("GET", "/",
                      env: {'REMOTE_ADDR'=>'192.168.0.1'})
        ok {K8::Request.new(env).client_ip_addr} == '192.168.0.1'
      end

    end


    topic '#scheme' do

      spec "[!jytwy] returns 'https' when env['HTTPS'] is 'on'." do
        env = new_env("GET", "/", env: {'HTTPS'=>'on'})
        ok {K8::Request.new(env).scheme} == 'https'
      end

      spec "[!zg8r2] returns env['rack.url_scheme'] ('http' or 'https')." do
        env = new_env("GET", "/", env: {'HTTPS'=>'off'})
        env['rack.url_scheme'] = 'http'
        ok {K8::Request.new(env).scheme} == 'http'
        env['rack.url_scheme'] = 'https'
        ok {K8::Request.new(env).scheme} == 'https'
      end

    end


    topic '#params_query' do

      spec "[!6ezqw] parses QUERY_STRING and returns it as Hash object." do
        qstr = "x=1&y=2"
        req = K8::Request.new(new_env("GET", "/", env: {'QUERY_STRING'=>qstr}))
        ok {req.params_query()} == {'x'=>'1', 'y'=>'2'}
      end

      spec "[!o0ws7] unquotes both keys and values." do
        qstr = "arr%5Bxxx%5D=%3C%3E+%26%3B"
        req = K8::Request.new(new_env("GET", "/", env: {'QUERY_STRING'=>qstr}))
        ok {req.params_query()} == {'arr[xxx]'=>'<> &;'}
      end

    end


    topic '#params_form' do

      spec "[!q88w9] raises error when content length is missing." do
        env = new_env("POST", "/", form: "x=1")
        env['CONTENT_LENGTH'] = nil
        req = K8::Request.new(env)
        pr = proc { req.params_form }
        ok {pr}.raise?(K8::HttpException, 'Content-Length header expected.')
      end

      spec "[!gi4qq] raises error when content length is invalid." do
        env = new_env("POST", "/", form: "x=1")
        env['CONTENT_LENGTH'] = "abc"
        req = K8::Request.new(env)
        pr = proc { req.params_form }
        ok {pr}.raise?(K8::HttpException, 'Content-Length should be an integer.')
      end

      spec "[!59ad2] parses form parameters and returns it as Hash object when form requested." do
        form = "x=1&y=2&arr%5Bxxx%5D=%3C%3E+%26%3B"
        req = K8::Request.new(new_env("POST", "/", form: form))
        ok {req.params_form} == {'x'=>'1', 'y'=>'2', 'arr[xxx]'=>'<> &;'}
      end

      spec "[!puxlr] raises error when content length is too long (> 10MB)." do
        env = new_env("POST", "/", form: "x=1")
        env['CONTENT_LENGTH'] = (10*1024*1024 + 1).to_s
        req = K8::Request.new(env)
        pr = proc { req.params_form }
        ok {pr}.raise?(K8::HttpException, 'Content-Length is too long.')
      end

    end


    topic '#params_multipart' do

      spec "[!y1jng] parses multipart when multipart form requested." do
        |multipart_env, data_dir|
        env = multipart_env
        req = K8::Request.new(env)
        form, files = req.params_multipart
        ok {form} == {
          "text1" => "test1",
          "text2" => "日本語\r\nあいうえお\r\n".force_encoding('binary'),
          "file1" => "example1.png",
          "file2" => "example1.jpg",
        }
        ok {files}.is_a?(Hash)
        ok {files.keys.sort} == ["file1", "file2"]
        #
        ok {files['file1']}.is_a?(K8::UploadedFile)
        ok {files['file1'].filename}     == "example1.png"
        ok {files['file1'].content_type} == "image/png"
        ok {files['file1'].tmp_filepath}.file_exist?
        expected = File.read("#{data_dir}/example1.png",  encoding: 'binary')
        actual   = File.read(files['file1'].tmp_filepath, encoding: 'binary')
        ok {actual} == expected
        #
        ok {files['file2']}.is_a?(K8::UploadedFile)
        ok {files['file2'].filename}     == "example1.jpg"
        ok {files['file2'].content_type} == "image/jpeg"
        ok {files['file2'].tmp_filepath}.file_exist?
        expected = File.read("#{data_dir}/example1.jpg",  encoding: 'binary')
        actual   = File.read(files['file2'].tmp_filepath, encoding: 'binary')
        ok {actual} == expected

      end

      spec "[!mtx6t] raises error when content length of multipart is too long (> 100MB)." do
        |multipart_env|
        env = multipart_env
        env['CONTENT_LENGTH'] = (100*1024*1024 + 1).to_s
        req = K8::Request.new(env)
        pr = proc { req.params_multipart }
        ok {pr}.raise?(K8::HttpException, 'Content-Length of multipart is too long.')
      end

    end


    topic '#params_json' do

      spec "[!ugik5] parses json data and returns it as hash object when json data is sent." do
        data = '{"x":1,"y":2,"arr":["a","b","c"]}'
        req = K8::Request.new(new_env("POST", "/", json: data))
        ok {req.params_json} == {"x"=>1, "y"=>2, "arr"=>["a", "b", "c"]}
      end

    end


    topic '#params' do

      spec "[!erlc7] parses QUERY_STRING when request method is GET or HEAD." do
        qstr = "a=8&b=9"
        form = "x=1&y=2"
        req = K8::Request.new(new_env('GET', '/', query: qstr, form: form))
        ok {req.params} == {"a"=>"8", "b"=>"9"}
      end

      spec "[!cr0zj] parses JSON when content type is 'application/json'." do
        qstr = "a=8&b=9"
        json = '{"n":123}'
        req = K8::Request.new(new_env('POST', '/', query: qstr, json: json))
        ok {req.params} == {"n"=>123}
      end

      spec "[!j2lno] parses form parameters when content type is 'application/x-www-form-urlencoded'." do
        qstr = "a=8&b=9"
        form = "x=1&y=2"
        req = K8::Request.new(new_env('POST', '/', query: qstr, form: form))
        ok {req.params} == {"x"=>"1", "y"=>"2"}
      end

      spec "[!4rmn9] parses multipart when content type is 'multipart/form-data'."

    end


    topic '#cookies' do

      spec "[!c9pwr] parses cookie data and returns it as hash object." do
        req = K8::Request.new(new_env('POST', '/', cookies: "aaa=homhom; bbb=madmad"))
        ok {req.cookies} == {"aaa"=>"homhom", "bbb"=>"madmad"}
      end

    end


    topic '#clear()' do

      spec "[!0jdal] removes uploaded files." do
        |multipart_env|
        req = K8::Request.new(multipart_env)
        form, files = req.params_multipart
        ok {files.empty?} == false
        tmpfile1 = files['file1'].tmp_filepath
        tmpfile2 = files['file2'].tmp_filepath
        ok {tmpfile1}.file_exist?
        ok {tmpfile2}.file_exist?
        #
        req.clear()
        ok {tmpfile1}.NOT.file_exist?
        ok {tmpfile2}.NOT.file_exist?
      end

    end


  end


  topic K8::Response do
  end


  topic 'K8::REQUEST_CLASS=' do

    spec "[!7uqb4] changes default request class." do
      original = K8::REQUEST_CLASS
      begin
        K8.REQUEST_CLASS = Array
        ok {K8::REQUEST_CLASS} == Array
      ensure
        K8.REQUEST_CLASS = original
      end
    end

  end


  topic 'K8::RESPONSE_CLASS=' do

    spec "[!c1bd0] changes default response class." do
      original = K8::RESPONSE_CLASS
      begin
        K8.RESPONSE_CLASS = Hash
        ok {K8::RESPONSE_CLASS} == Hash
      ensure
        K8.RESPONSE_CLASS = original
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
        req    = K8::Request.new(new_env("GET", "/books"))
        resp   = K8::Response.new()
        action = K8::BaseAction.new(req, resp)
        ok {action.instance_variable_get('@req')}.same?(req)
        ok {action.instance_variable_get('@resp')}.same?(resp)
      end

      spec "[!7sfyf] sets session object." do
        d = {'a'=>1}
        req    = K8::Request.new(new_env("GET", "/books", env: {'rack.session'=>d}))
        resp   = K8::Response.new()
        action = K8::BaseAction.new(req, resp)
        ok {action.instance_variable_get('@sess')}.same?(d)
        ok {action.sess}.same?(d)
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


    topic '.mapping()' do

      spec "[!o148k] maps urlpath pattern and request methods." do
        cls = Class.new(K8::BaseAction) do
          mapping '',        :GET=>:do_index, :POST=>:do_create
          mapping '/{code}', :GET=>:do_show, :PUT=>:do_update
        end
        args_list = []
        cls._action_method_mapping.each do |*args|
          args_list << args
        end
        ok {args_list} == [
          ["",        {:GET=>:do_index, :POST=>:do_create}],
          ["/{code}", {:GET=>:do_show,  :PUT=>:do_update}],
        ]
      end

    end


    topic '._build_action_info()' do

      spec "[!ordhc] build ActionInfo objects for each action methods." do
        infos = BooksAction._build_action_info('/api/books')
        #
        ok {infos[:do_index]}.is_a?(K8::ActionInfo)
        ok {infos[:do_index].meth} == :GET
        ok {infos[:do_index].path} == '/api/books/'
        #
        ok {infos[:do_update]}.is_a?(K8::ActionInfo)
        ok {infos[:do_update].meth} == :PUT
        ok {infos[:do_update].path(123)} == '/api/books/123'
      end

    end


    topic '.[]' do

      spec "[!1tq8z] returns ActionInfo object corresponding to action method." do
        BooksAction._build_action_info('/api/books')
        cls = BooksAction
        #
        ok {cls[:do_create]}.is_a?(K8::ActionInfo)
        ok {cls[:do_create].meth} == :POST
        ok {cls[:do_create].path} == '/api/books/'
        #
        ok {cls[:do_show]}.is_a?(K8::ActionInfo)
        ok {cls[:do_show].meth} == :GET
        ok {cls[:do_show].path(123)} == '/api/books/123'
      end

      spec "[!6g2iw] returns nil when not mounted yet." do
        class ExampleClass2 < K8::BaseAction
          mapping '', :GET=>:do_index
          def do_index; end
        end
        ok {ExampleClass2[:do_index]} == nil
      end

    end


  end


  topic K8::Action do

    fixture :action_obj do
      env = new_env("GET", "/", env: {'rack.session'=>{}})
      BooksAction.new(K8::Request.new(env), K8::Response.new())
    end


    topic '#request' do

      spec "[!siucz] request object is accessable with 'request' method as well as 'req'." do
        |action_obj|
        ok {action_obj.request}.same?(action_obj.req)
      end

    end


    topic '#response' do

      spec "[!qnzp6] response object is accessable with 'response' method as well as 'resp'." do
        |action_obj|
        ok {action_obj.response}.same?(action_obj.resp)
      end

    end


    topic '#session' do

      spec "[!bd3y4] session object is accessable with 'session' method as well as 'sess'." do
        |action_obj|
        ok {action_obj.session}.same?(action_obj.sess)
        ok {action_obj.session} != nil
      end

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


    topic '#invoke_action()' do

      spec "[!d5v0l] handles exception when handler method defined." do
        env = new_env("POST", "/", env: {'rack.session'=>{}})
        action_obj = TestExceptionAction.new(K8::Request.new(env), K8::Response.new())
        result = nil
        pr = proc { result = action_obj.handle_action(:do_create, []) }
        ok {pr}.raise?(ZeroDivisionError)
        #
        action_obj.instance_exec(self) do |_|
          def on_ZeroDivisionError(ex)
            @_called = ex
            "<h1>Yes</h1>"
          end
        end
        ok {action_obj}.respond_to?('on_ZeroDivisionError')
        ok {pr}.NOT.raise?(ZeroDivisionError)
        ok {action_obj.instance_variable_get('@_called')} != nil
        ok {action_obj.instance_variable_get('@_called')}.is_a?(ZeroDivisionError)
        ok {result} == ["<h1>Yes</h1>"]
      end

    end


    topic '#handle_content()' do

      case_when "[!jhnzu] when content is nil..." do

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
            handle_content("<b>")
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

        spec "[!5q1u5] raises error when failed to detect content type." do
          |action_obj|
          action_obj.instance_exec(self) do |_|
            pr = proc { handle_content("html") }
            _.ok {pr}.raise?(K8::ContentTypeRequiredError, "Content-Type response header required.")
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


    topic '#detect_content_type()' do

      spec "[!onjro] returns 'text/html; charset=utf-8' when text starts with '<'." do
        |action_obj|
        action_obj.instance_exec(self) do |_|
          ctype = 'text/html; charset=utf-8'
          _.ok {detect_content_type("<p>Hello</p>")}     == ctype
          _.ok {detect_content_type("\n\n<p>Hello</p>")} == ctype
        end
      end

      spec "[!qiugc] returns 'application/json' when text starts with '{'." do
        |action_obj|
        action_obj.instance_exec(self) do |_|
          ctype = 'application/json'
          _.ok {detect_content_type("{\"a\":1}")}     == ctype
          _.ok {detect_content_type("\n\n{\"a\":1}")} == ctype
        end
      end

      spec "[!zamnv] returns nil when text starts with neight '<' nor '{'." do
        |action_obj|
        action_obj.instance_exec(self) do |_|
          _.ok {detect_content_type("hoomhom")}    == nil
          _.ok {detect_content_type("\n\nhomhom")} == nil
        end
      end

    end


    topic '#set_flash_message()' do

      spec "[!9f0iv] sets flash message into session." do
        |action_obj|
        action_obj.instance_exec(self) do |_|
          @sess = {}
          action_obj.set_flash_message("homhom")
          _.ok {@sess} == {"_flash"=>"homhom"}
        end
      end

    end


    topic '#get_flash_message()' do

      spec "[!5minm] returns flash message stored in session." do
        |action_obj|
        action_obj.instance_exec(self) do |_|
          @sess = {}
          action_obj.set_flash_message("homhom")
          _.ok {action_obj.get_flash_message()} == "homhom"
        end
      end

      spec "[!056bp] deletes flash message from sesson." do
        |action_obj|
        action_obj.instance_exec(self) do |_|
          @sess = {}
          action_obj.set_flash_message("homhom")
          _.ok {@sess.empty?} == false
          action_obj.get_flash_message()
          _.ok {@sess.empty?} == true
        end
      end

    end


    topic '#redirect_to()' do

      spec "[!ev9nu] sets response status code as 302." do
        |action_obj|
        action_obj.instance_exec(self) do |_|
          redirect_to '/top'
          _.ok {@resp.status} == 302
          redirect_to '/top', 301
          _.ok {@resp.status} == 301
        end
      end

      spec "[!spfge] sets Location response header." do
        |action_obj|
        action_obj.instance_exec(self) do |_|
          redirect_to '/top'
          _.ok {@resp.headers['Location']} == '/top'
        end
      end

      spec "[!k3gvm] returns html anchor tag." do
        |action_obj|
        action_obj.instance_exec(self) do |_|
          ret = redirect_to '/top?x=1&y=2'
          _.ok {ret} == '<a href="/top?x=1&amp;y=2">/top?x=1&amp;y=2</a>'
        end
      end

      spec "[!xkrfk] sets flash message if provided." do
        |action_obj|
        action_obj.instance_exec(self) do |_|
          redirect_to '/top', flash: "created!"
          _.ok {get_flash_message()} == "created!"
        end
      end

    end


    topic '#validation_failed()' do

      spec "[!texnd] sets response status code as 422." do
        |action_obj|
        action_obj.instance_exec(self) do |_|
          validation_failed()
          _.ok {@resp.status} == 422
        end
      end

    end


    topic '#csrf_protection_required?' do

      fixture :action_obj do
        env = new_env('GET', '/')
        action = K8::Action.new(K8::Request.new(env), K8::Response.new)
      end

      spec "[!8chgu] returns false when requested with 'XMLHttpRequest'." do
        headers = {'X-Requested-With'=>'XMLHttpRequest'}
        env = new_env('GET', '/', headers: headers)
        action = K8::Action.new(K8::Request.new(env), K8::Response.new)
        action.instance_exec(self) do |_|
          _.ok {csrf_protection_required?} == false
        end
      end

      spec "[!vwrqv] returns true when request method is one of POST, PUT, or DELETE." do
        ['POST', 'PUT', 'DELETE'].each do |meth|
          env = new_env(meth, '/')
          action = K8::Action.new(K8::Request.new(env), K8::Response.new)
          action.instance_exec(self) do |_|
            _.ok {csrf_protection_required?} == true
          end
        end
      end

      spec "[!jfhla] returns true when request method is GET or HEAD." do
        ['GET', 'HEAD'].each do |meth|
          env = new_env(meth, '/')
          action = K8::Action.new(K8::Request.new(env), K8::Response.new)
          action.instance_exec(self) do |_|
            _.ok {csrf_protection_required?} == false
          end
        end
      end

    end


    topic '#csrf_protection()' do

      spec "[!h5tzb] raises nothing when csrf token matched." do
        headers = {'Cookie'=>"_csrf=abc123"}
        form    = {"_csrf"=>"abc123"}
        env = new_env('POST', '/', form: form, headers: headers)
        action = K8::Action.new(K8::Request.new(env), K8::Response.new)
        action.instance_exec(self) do |_|
          pr = proc { csrf_protection() }
          _.ok {pr}.NOT.raise?
        end
      end

      spec "[!h0e0q] raises HTTP 400 when csrf token mismatched." do
        headers = {'Cookie'=>"_csrf=abc123"}
        form    = {"_csrf"=>"abc999"}
        env = new_env('POST', '/', form: form, headers: headers)
        action = K8::Action.new(K8::Request.new(env), K8::Response.new)
        action.instance_exec(self) do |_|
          pr = proc { csrf_protection() }
          _.ok {pr}.raise?(K8::HttpException, "invalid csrf token")
        end
      end

    end


    topic '#csrf_get_token()' do

      spec "[!mr6md] returns csrf cookie value." do
        |action_obj|
        action_obj.instance_exec(self) do |_|
          @req.env['HTTP_COOKIE'] = "_csrf=abc123"
          _.ok {csrf_get_token()} == "abc123"
        end
      end

    end


    topic '#csrf_set_token()' do

      spec "[!8hm2o] sets csrf cookie and returns token." do
        |action_obj|
        action_obj.instance_exec(self) do |_|
          ret = csrf_set_token("abcdef123456")
          _.ok {@resp.headers['Set-Cookie']} == "_csrf=abcdef123456"
          _.ok {ret} == "abcdef123456"
        end
      end

    end


    topic '#csrf_get_param()' do

      spec "[!pal33] returns csrf token in request parameter." do
        env = new_env("POST", "/", form: {"_csrf"=>"foobar999"})
        action_obj = K8::Action.new(K8::Request.new(env), K8::Response.new)
        action_obj.instance_exec(self) do |_|
          _.ok {csrf_get_param()} == "foobar999"
        end
      end

    end


    topic '#csrf_new_token()' do

      spec "[!zl6cl] returns new random token." do
        |action_obj|
        tokens = []
        n = 1000
        action_obj.instance_exec(self) do |_|
          n.times { tokens << csrf_new_token() }
        end
        ok {tokens.sort.uniq.length} == n
      end

      spec "[!sfgfx] uses SHA1 + urlsafe BASE64." do
        |action_obj|
        action_obj.instance_exec(self) do |_|
          token = (1..5).each.map { csrf_new_token() }.find {|x| x =~ /[^a-fA-F0-9]/ }
          _.ok {token} != nil
          _.ok {token} =~ /\A[-_a-zA-Z0-9]+\z/   # uses urlsafe BASE64
          _.ok {token.length} == 27              # == SHA1.length - "=".length
        end
      end

    end


    topic '#csrf_token()' do

      spec "[!7gibo] returns current csrf token." do
        |action_obj|
        action_obj.instance_exec(self) do |_|
          token = csrf_token()
          _.ok {token} =~ /\A[-_a-zA-Z0-9]{27}\z/
          _.ok {csrf_token()} == token
          _.ok {csrf_token()} == token
        end
      end

      spec "[!6vtqd] creates new csrf token and set it to cookie when csrf token is blank." do
        |action_obj|
        action_obj.instance_exec(self) do |_|
          _.ok {@resp.headers['Set-Cookie']} == nil
          token = csrf_token()
          _.ok {@resp.headers['Set-Cookie']} == "_csrf=#{token}"
        end
      end

    end


    topic '#send_file()' do

      fixture :data_dir do
        File.join(File.dirname(__FILE__), 'data')
      end

      fixture :pngfile do |data_dir|
        File.join(data_dir, 'example1.png')
      end

      fixture :jpgfile do |data_dir|
        File.join(data_dir, 'example1.jpg')
      end

      fixture :jsfile do |data_dir|
        File.join(data_dir, 'wabisabi.js')
      end

      spec "[!37i9c] returns opened file." do
        |action_obj, jpgfile|
        action_obj.instance_exec(self) do |_|
          file = send_file(jpgfile)
          _.ok {file}.is_a?(File)
          _.ok {file.closed?} == false
          _.ok {file.path} == jpgfile
        end
      end

      spec "[!v7r59] returns nil with status code 304 when not modified." do
        |action_obj, pngfile|
        mtime_utc_str = K8::Util.http_utc_time(File.mtime(pngfile).utc)
        action_obj.instance_exec(self) do |_|
          @req.env['HTTP_IF_MODIFIED_SINCE'] = mtime_utc_str
          ret = send_file(pngfile)
          _.ok {ret} == nil
          _.ok {@resp.status} == 304
        end
      end

      case_when "[!woho6] when gzipped file exists..." do

        spec "[!9dmrf] returns gzipped file object when 'Accept-Encoding: gzip' exists." do
          |action_obj, jsfile|
          action_obj.instance_exec(self) do |_|
            file = send_file(jsfile)
            _.ok {file}.is_a?(File)
            _.ok {file.path} == jsfile   # not gzipped
            #
            @req.env['HTTP_ACCEPT_ENCODING'] = 'gzip,deflate'
            file = send_file(jsfile)
            _.ok {file}.is_a?(File)
            _.ok {file.path} == jsfile + ".gz"
          end
        end

        spec "[!m51dk] adds 'Content-Encoding: gzip' when 'Accept-Encoding: gzip' exists." do
          |action_obj, jsfile|
          action_obj.instance_exec(self) do |_|
            @resp.headers.clear()
            send_file(jsfile)
            _.ok {@resp.headers['Content-Encoding']} == nil
            _.ok {@resp.headers['Content-Type']} == 'application/javascript'
            _.ok {@resp.status} == 200
            #
            @resp.headers.clear()
            @req.env['HTTP_ACCEPT_ENCODING'] = 'gzip,deflate'
            send_file(jsfile)
            _.ok {@resp.headers['Content-Encoding']} == 'gzip'
            _.ok {@resp.headers['Content-Type']} == 'application/javascript'
            _.ok {@resp.status} == 200
          end
        end

      end


      spec "[!e8l5o] sets Content-Type with guessing it from filename." do
        |action_obj, pngfile, jpgfile|
        action_obj.instance_exec(self) do |_|
          send_file(pngfile)
          _.ok {@resp.headers['Content-Type']} == "image/png"
          #
          send_file(jpgfile)
          _.ok {@resp.headers['Content-Type']} == "image/png"   # not changed
          #
          @resp.headers['Content-Type'] = nil
          send_file(jpgfile)
          _.ok {@resp.headers['Content-Type']} == "image/jpeg"  # changed!
        end
      end

      spec "[!qhx0l] sets Content-Length with file size." do
        |action_obj, pngfile, jpgfile|
        action_obj.instance_exec(self) do |_|
          send_file(pngfile)
          _.ok {@resp.headers['Content-Length']} == File.size(pngfile).to_s
          send_file(jpgfile)
          _.ok {@resp.headers['Content-Length']} == File.size(jpgfile).to_s
        end
      end

      spec "[!6j4fh] sets Last-Modified with file timestamp." do
        |action_obj, pngfile|
        expected = K8::Util.http_utc_time(File.mtime(pngfile).utc)
        action_obj.instance_exec(self) do |_|
          send_file(pngfile)
          _.ok {@resp.headers['Last-Modified']} == expected
        end
      end

      spec "[!iblvb] raises 404 Not Found when file not exist." do
        |action_obj|
        action_obj.instance_exec(self) do |_|
          pr = proc { send_file('hom-hom.hom') }
          _.ok {pr}.raise?(K8::HttpException)
          _.ok {pr.exception.status_code} == 404
        end
      end

    end


  end


  topic K8::ActionInfo do


    topic '.create()' do

      spec "[!1nk0i] replaces urlpath parameters with '%s'." do
        info = K8::ActionInfo.create('GET', '/books/{id}/comments/{comment_id}')
        actual = info.instance_variable_get('@urlpath_format')
        ok {actual} == '/books/%s/comments/%s'
        #
        info = K8::ActionInfo.create('GET', '/books')
        actual = info.instance_variable_get('@urlpath_format')
        ok {actual} == '/books'
      end

      spec "[!a7fqv] replaces '%' with'%%'." do
        info = K8::ActionInfo.create('GET', '/books%9A%9B/{id}')
        actual = info.instance_variable_get('@urlpath_format')
        ok {actual} == '/books%%9A%%9B/%s'
      end

      spec "[!btt2g] returns ActionInfoN object when number of urlpath parameter <= 4." do
        info = K8::ActionInfo.create('GET', '/books')
        ok {info}.is_a?(K8::ActionInfo0)
        ok {info.path} == '/books'
        ok {->{ info.path('a') }}.raise?(ArgumentError, "wrong number of arguments (1 for 0)")
        #
        info = K8::ActionInfo.create('GET', '/books/{id}')
        ok {info}.is_a?(K8::ActionInfo1)
        ok {info.path('a')} == '/books/a'
        ok {->{ info.path() }}.raise?(ArgumentError, "wrong number of arguments (0 for 1)")
        #
        info = K8::ActionInfo.create('GET', '/books/{id}/comments/{comment_id}')
        ok {info}.is_a?(K8::ActionInfo2)
        ok {info.path('a', 'b')} == '/books/a/comments/b'
        ok {->{info.path('a')}}.raise?(ArgumentError, "wrong number of arguments (1 for 2)")
        #
        info = K8::ActionInfo.create('GET', '/books/{id}/{title}/{code}')
        ok {info}.is_a?(K8::ActionInfo3)
        ok {info.path('a', 'b', 'c')} == '/books/a/b/c'
        ok {->{info.path(1,2)}}.raise?(ArgumentError, "wrong number of arguments (2 for 3)")
        #
        info = K8::ActionInfo.create('GET', '/books/{id}/{title}/{code}/{ref}')
        ok {info}.is_a?(K8::ActionInfo4)
        ok {info.path('a', 'b', 'c', 'd')} == '/books/a/b/c/d'
        ok {->{info.path}}.raise?(ArgumentError, "wrong number of arguments (0 for 4)")
      end

      spec "[!x5yx2] returns ActionInfo object when number of urlpath parameter > 4." do
        info = K8::ActionInfo.create('GET', '/books/{id}/{title}/{code}/{ref}/{x}')
        ok {info}.is_a?(K8::ActionInfo)
        ok {info.path('a', 'b', 'c', 'd', 'e')} == "/books/a/b/c/d/e"
        #
        ok {->{info.path('a','b','c')}}.raise?(ArgumentError, "too few arguments")
      end

    end


    topic '#form_action_attr()' do

      spec "[!qyhkm] returns '/api/books/123' when method is POST." do
        info = K8::ActionInfo.create('POST', '/api/books/{id}')
        ok {info.form_action_attr(123)} == '/api/books/123'
      end

      spec "[!kogyx] returns '/api/books/123?_method=PUT' when method is not POST." do
        info = K8::ActionInfo.create('PUT', '/api/books/{id}')
        ok {info.form_action_attr(123)} == '/api/books/123?_method=PUT'
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

    spec "[!i51id] registers '\d+' as default pattern of param 'id' or /_id\z/." do
      pat, proc_ = K8::DEFAULT_PATTERNS.lookup('id')
      ok {pat} == '\d+'
      ok {proc_.call("123")} == 123
      pat, proc_ = K8::DEFAULT_PATTERNS.lookup('book_id')
      ok {pat} == '\d+'
      ok {proc_.call("123")} == 123
    end

    spec "[!2g08b] registers '(?:\.\w+)?' as default pattern of param 'ext'." do
      pat, proc_ = K8::DEFAULT_PATTERNS.lookup('ext')
      ok {pat} == '(?:\.\w+)?'
      ok {proc_} == nil
    end

    spec "[!8x5mp] registers '\d\d\d\d-\d\d-\d\d' as default pattern of param 'date' or /_date\z/." do
      pat, proc_ = K8::DEFAULT_PATTERNS.lookup('date')
      ok {pat} == '\d\d\d\d-\d\d-\d\d'
      ok {proc_.call("2014-12-24")} == Date.new(2014, 12, 24)
      pat, proc_ = K8::DEFAULT_PATTERNS.lookup('birth_date')
      ok {pat} == '\d\d\d\d-\d\d-\d\d'
      ok {proc_.call("2015-02-14")} == Date.new(2015, 2, 14)
    end

    spec "[!wg9vl] raises 404 error when invalid date (such as 2012-02-30)." do
      pat, proc_ = K8::DEFAULT_PATTERNS.lookup('date')
      pr = proc { proc_.call('2012-02-30') }
      ok {pr}.raise?(K8::HttpException, "2012-02-30: invalid date.")
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


    topic '#each()' do

      spec "[!62y5q] yields each urlpath pattern and action methods." do
        |mapping, methods1, methods2|
        arr = []
        mapping.each do |urlpath_pat, action_methods|
          arr << [urlpath_pat, action_methods]
        end
        ok {arr} == [
          ['/',         methods1],
          ['/{id:\d+}', methods2],
        ]
      end

    end


  end


  topic K8::ActionMapping do


    topic '#initialize()' do

      spec "[!buj0d] prepares LRU cache if cache size specified." do
        mapping = K8::ActionMapping.new([], urlpath_cache_size: 3)
        mapping.instance_exec(self) do |_|
          _.ok {@urlpath_cache_size} == 3
          _.ok {@urlpath_lru_cache}  == {}
        end
        #
        mapping = K8::ActionMapping.new([], urlpath_cache_size: 0)
        mapping.instance_exec(self) do |_|
          _.ok {@urlpath_cache_size} == 0
          _.ok {@urlpath_lru_cache}  == nil
        end
      end

      spec "[!wsz8g] compiles urlpath mapping passed." do
        mapping = K8::ActionMapping.new([
            ['/api/books', BooksAction],
        ])
        mapping.instance_exec(self) do |_|
          _.ok {@urlpath_rexp} == %r'\A/api/books(?:/\d+(\z)|/\d+/edit(\z))\z'
          _.ok {@fixed_endpoints.keys} == ['/api/books/', '/api/books/new']
          _.ok {@variable_endpoints.map{|x| x[0]}} == ['/api/books/{id}', '/api/books/{id}/edit']
        end
      end

    end


    topic '#compile()' do

      fixture :proc1 do
        proc {|x| x.to_i }
      end

      fixture :proc2 do
        proc {|x| x.to_i }
      end

      fixture :mapping do
        |proc1, proc2|
        dp = K8::DefaultPatterns.new
        dp.register('id',    '\d+', &proc1)
        dp.register(/_id\z/, '\d+', &proc2)
        K8::ActionMapping.new([
            ['/api', [
                ['/books', BooksAction],
                ['/books/{book_id}', BookCommentsAction],
            ]],
        ], default_patterns: dp)
      end

      spec "[!6f3vl] compiles urlpath mapping." do
        |mapping|
        mapping.instance_exec(self) do |_|
          _.ok {@urlpath_rexp}.is_a?(Regexp)
          _.ok {@urlpath_rexp} == Regexp.compile('
                 \A/api
                    (?: /books
                          (?: /\d+(\z) | /\d+/edit(\z) )
                     |  /books/\d+
                          (?: /comments(\z) | /comments/\d+(\z) )
                    )
                 \z'.gsub(/\s/, ''))
          _.ok {@fixed_endpoints.keys} == ["/api/books/", "/api/books/new"]
          _.ok {@variable_endpoints.map{|x| x[0..2] }} == [
            ["/api/books/{id}", BooksAction, {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete}],
            ["/api/books/{id}/edit", BooksAction, {:GET=>:do_edit}],
            ["/api/books/{book_id}/comments", BookCommentsAction, {:GET=>:do_comments}],
            ["/api/books/{book_id}/comments/{comment_id}", BookCommentsAction, {:GET=>:do_comment}],
          ]
        end
      end

      spec "[!w45ad] can compile nested array." do
        |mapping, proc1, proc2|
        mapping.instance_exec(self) do |_|
          _.ok {@urlpath_rexp} == Regexp.compile('
            \A  /api
                    (?: /books
                            (?: /\d+(\z) | /\d+/edit(\z) )
                     |  /books/\d+
                            (?: /comments(\z) | /comments/\d+(\z) )
                    )
            \z'.gsub(/\s/, ''))
          _.ok {@variable_endpoints} == [
            ["/api/books/{id}",
              BooksAction,
              {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete},
              /\A\/api\/books\/(\d+)\z/,
              ["id"], [proc1],
            ],
            ["/api/books/{id}/edit",
              BooksAction,
              {:GET=>:do_edit},
              /\A\/api\/books\/(\d+)\/edit\z/,
              ["id"], [proc1],
            ],
            ["/api/books/{book_id}/comments",
              BookCommentsAction,
              {:GET=>:do_comments},
              /\A\/api\/books\/(\d+)\/comments\z/,
              ["book_id"], [proc2],
            ],
            ["/api/books/{book_id}/comments/{comment_id}",
              BookCommentsAction,
              {:GET=>:do_comment},
              /\A\/api\/books\/(\d+)\/comments\/(\d+)\z/,
              ["book_id", "comment_id"], [proc2, proc2],
            ],
          ]
          _.ok {@fixed_endpoints} == {
            "/api/books/"   =>["/api/books/", BooksAction, {:GET=>:do_index, :POST=>:do_create}, nil, nil, nil],
            "/api/books/new"=>["/api/books/new", BooksAction, {:GET=>:do_new}, nil, nil, nil],
          }
        end
      end

      spec "[!z2iax] classifies urlpath contains any parameter as variable one." do
        |mapping, proc1, proc2|
        mapping.instance_exec(self) do |_|
          _.ok {@variable_endpoints} == [
            ["/api/books/{id}",
              BooksAction,
              {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete},
              /\A\/api\/books\/(\d+)\z/,
              ["id"], [proc1],
            ],
            ["/api/books/{id}/edit",
              BooksAction,
              {:GET=>:do_edit},
              /\A\/api\/books\/(\d+)\/edit\z/,
              ["id"], [proc1],
            ],
            ["/api/books/{book_id}/comments",
              BookCommentsAction,
              {:GET=>:do_comments},
              /\A\/api\/books\/(\d+)\/comments\z/,
              ["book_id"], [proc2],
            ],
            ["/api/books/{book_id}/comments/{comment_id}",
              BookCommentsAction,
              {:GET=>:do_comment},
              /\A\/api\/books\/(\d+)\/comments\/(\d+)\z/,
              ["book_id", "comment_id"], [proc2, proc2],
            ],
          ]
        end
      end

      spec "[!rvdes] classifies urlpath contains no parameters as fixed one." do
        |mapping|
        mapping.instance_exec(self) do |_|
          _.ok {@fixed_endpoints} == {
            "/api/books/" => ["/api/books/", BooksAction, {:GET=>:do_index, :POST=>:do_create}, nil, nil, nil],
            "/api/books/new" => ["/api/books/new", BooksAction, {:GET=>:do_new}, nil, nil, nil],
          }
        end
      end

      spec "[!6xwhq] builds action infos for each action methods." do
        class Ex_6xwhq < K8::Action
          mapping '',      :GET=>:do_index, :POST=>:do_create
          mapping '/{id}', :GET=>:do_show,  :PUT=>:do_update
          def do_index; end
          def do_create; end
          def do_show(id); end
          def do_update(id); end
        end
        ok {Ex_6xwhq[:do_create]} == nil
        ok {Ex_6xwhq[:do_update]} == nil
        #
        K8::ActionMapping.new([
            ['/test', [
                ['/example4', Ex_6xwhq],
            ]],
        ])
        #
        ok {Ex_6xwhq[:do_create]} != nil
        ok {Ex_6xwhq[:do_create].meth} == :POST
        ok {Ex_6xwhq[:do_create].path} == '/test/example4'
        ok {Ex_6xwhq[:do_update]} != nil
        ok {Ex_6xwhq[:do_update].meth} == :PUT
        ok {Ex_6xwhq[:do_update].path(123)} == '/test/example4/123'
      end

      spec "[!wd2eb] accepts subclass of Action class." do
        _, proc1 = K8::DEFAULT_PATTERNS.lookup('id')
        _, proc2 = K8::DEFAULT_PATTERNS.lookup('book_id')
        mapping = K8::ActionMapping.new([
            ['/api/books', BooksAction],
            ['/api/books/{book_id}', BookCommentsAction],
        ])
        mapping.instance_exec(self) do |_|
          _.ok {@urlpath_rexp} == Regexp.compile('
            \A  (?: /api/books
                       (?: /\d+(\z) | /\d+/edit(\z) )
                 |  /api/books/\d+
                       (?: /comments(\z) | /comments/\d+(\z) )
                )
            \z'.gsub(/\s/, ''))
          _.ok {@fixed_endpoints} == {
            "/api/books/"   =>["/api/books/", BooksAction, {:GET=>:do_index, :POST=>:do_create}, nil, nil, nil],
            "/api/books/new"=>["/api/books/new", BooksAction, {:GET=>:do_new}, nil, nil, nil],
          }
          _.ok {@variable_endpoints} == [
            ["/api/books/{id}",
              BooksAction,
              {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete},
              /\A\/api\/books\/(\d+)\z/,
              ["id"], [proc1],
            ],
            ["/api/books/{id}/edit",
              BooksAction,
              {:GET=>:do_edit},
              /\A\/api\/books\/(\d+)\/edit\z/,
              ["id"], [proc1],
            ],
            ["/api/books/{book_id}/comments",
              BookCommentsAction,
              {:GET=>:do_comments},
              /\A\/api\/books\/(\d+)\/comments\z/,
              ["book_id"], [proc2],
            ],
            ["/api/books/{book_id}/comments/{comment_id}",
              BookCommentsAction,
              {:GET=>:do_comment},
              /\A\/api\/books\/(\d+)\/comments\/(\d+)\z/,
              ["book_id", "comment_id"], [proc2, proc2],
            ],
          ]
        end
      end

      spec "[!ue766] raises error when action method is not defined in action class." do
        |mapping|
        class ExampleAction3 < K8::Action
          mapping '', :GET=>:do_index, :POST=>:do_create
          def do_index; end
        end
        pr = proc { K8::ActionMapping.new([['/example3', ExampleAction3]]) }
        expected_msg = ":POST=>:do_create: unknown action method in ExampleAction3."
        ok {pr}.raise?(K8::UnknownActionMethodError, expected_msg)
      end

      spec "[!l2kz5] requires library when filepath and classname specified." do
        dirname  = "test_l2kz5"
        filename = dirname + "/sample.rb"
        content = <<-END
        require 'keight'
        module Ex_l2kz5
          class Example_l2kz5 < K8::Action
            mapping '',      :GET=>:do_index
            mapping '/{id}', :GET=>:do_show
            def do_index; end
            def do_show(id); end
          end
        end
        END
        Dir.mkdir(dirname) unless File.directory?(dirname)
        File.open(filename, 'w') {|f| f << content }
        at_end { File.unlink filename; Dir.rmdir dirname }
        #
        _, proc1 = K8::DEFAULT_PATTERNS.lookup('id')
        _, proc2 = K8::DEFAULT_PATTERNS.lookup('book_id')
        mapping = K8::ActionMapping.new([
            ['/api/example', './test_l2kz5/sample:Ex_l2kz5::Example_l2kz5'],
        ])
        mapping.instance_exec(self) do |_|
          _.ok {@fixed_endpoints} == {
            "/api/example"=>["/api/example", Ex_l2kz5::Example_l2kz5, {:GET=>:do_index}, nil, nil, nil],
          }
          _.ok {@variable_endpoints} == [
            ["/api/example/{id}", Ex_l2kz5::Example_l2kz5, {:GET=>:do_show}, /\A\/api\/example\/(\d+)\z/, ["id"], [proc1]],
          ]
        end
      end

      spec "[!irt5g] raises TypeError when unknown object specified." do
        pr = proc do
          mapping = K8::ActionMapping.new([
              ['/api/example', {:GET=>:do_index}],
          ])
        end
        ok {pr}.raise?(TypeError, "Action class or nested array expected, but got {:GET=>:do_index}")
      end

      spec "[!bcgc9] skips classes which have only fixed urlpaths." do
        klass = Class.new(K8::Action) do
          mapping '/', :GET=>:do_index
          mapping '/new', :GET=>:do_new
          def do_index; end
          def do_new; end
        end
        mapping = K8::ActionMapping.new([
            ['/api', [
                ['/books', BooksAction],
                ['/samples', klass],
                ['/books/{book_id}', BookCommentsAction],
            ]],
        ])
        mapping.instance_exec(self) do |_|
          _.ok {@urlpath_rexp} == Regexp.compile('
              \A  /api
                      (?:  /books
                               (?:/\d+(\z)|/\d+/edit(\z))
                      |    /books/\d+
                               (?:/comments(\z)|/comments/\d+(\z))
                      )
              \z'.gsub(/\s+/, ''))
          _.ok {@fixed_endpoints['/api/samples/']} == ["/api/samples/", klass, {:GET=>:do_index}, nil, nil, nil]
          _.ok {@fixed_endpoints['/api/samples/new']} == ["/api/samples/new", klass, {:GET=>:do_new}, nil, nil, nil]
        end
      end

      spec "[!169ad] removes unnecessary grouping." do
        klass = Class.new(K8::Action) do
          mapping '/{id}', :GET=>:do_show
          def do_show(id); end
        end
        mapping = K8::ActionMapping.new([
            ['/api', [
                ['/test', klass],
            ]],
        ])
        mapping.instance_exec(self) do |_|
          #_.ok {@urlpath_rexp} == %r'\A(?:/api(?:/test(?:/\d+(\z))))\z'
          _.ok {@urlpath_rexp} == %r'\A/api/test/\d+(\z)\z'
        end
      end

    end


    topic '#dispatch()' do

      fixture :proc1 do
        proc {|x| x.to_i }
      end

      fixture :mapping do
        |proc1|
        dp = K8::DefaultPatterns.new
        dp.register('id',   '\d+', &proc1)
        dp.register(/_id$/, '\d+', &proc1)
        K8::ActionMapping.new([
            ['/api', [
                ['/books', BooksAction],
                ['/books/{book_id}', BookCommentsAction],
            ]],
        ], default_patterns: dp, urlpath_cache_size: 3)
      end

      spec "[!jyxlm] returns action class and methods, parameter names and values." do
        |mapping|
        tuple = mapping.dispatch('/api/books/123')
        ok {tuple} == [BooksAction, {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete}, ['id'], [123]]
        tuple = mapping.dispatch('/api/books/123/comments/999')
        ok {tuple} == [BookCommentsAction, {:GET=>:do_comment}, ['book_id', 'comment_id'], [123, 999]]
      end

      spec "[!j34yh] finds from fixed urlpaths at first." do
        |mapping|
        mapping.instance_exec(self) do |_|
          _.ok {dispatch('/books')} == nil
          tuple = @fixed_endpoints['/api/books/']
          _.ok {tuple} != nil
          @fixed_endpoints['/books'] = tuple
          expected = [BooksAction, {:GET=>:do_index, :POST=>:do_create}, [], []]
          _.ok {dispatch('/books')} != nil
          _.ok {dispatch('/books')} == expected
          _.ok {dispatch('/api/books/')} == expected
        end
      end

      spec "[!95q61] finds from variable urlpath patterns when not found in fixed ones." do
        |mapping|
        ok {mapping.dispatch('/api/books/123')} == \
          [
            BooksAction,
            {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete},
            ["id"],
            [123],
          ]
        ok {mapping.dispatch('/api/books/123/comments/999')} == \
          [
            BookCommentsAction,
            {:GET=>:do_comment},
            ["book_id", "comment_id"],
            [123, 999],
          ]
      end

      spec "[!sos5i] returns nil when request path not matched to urlpath patterns." do
        |mapping|
        ok {mapping.dispatch('/api/booking')} == nil
      end

      spec "[!1k1k5] converts urlpath param values by converter procs." do
        |mapping|
        tuple = mapping.dispatch('/api/books/123')
        ok {tuple[2..3]} == [['id'], [123]]
        tuple = mapping.dispatch('/api/books/123/comments/999')
        ok {tuple[2..3]} == [['book_id', 'comment_id'], [123, 999]]
      end

      spec "[!uqwr7] stores result into cache if cache is enabled." do
        |mapping|
        tuple = mapping.dispatch('/api/books/111')
        mapping.instance_exec(self) do |_|
          _.ok {@urlpath_lru_cache} == {'/api/books/111' => tuple}
        end
      end

      spec "[!3ps5g] deletes item from cache when cache size over limit." do
        |mapping|
        mapping.dispatch('/api/books/1')
        mapping.dispatch('/api/books/2')
        mapping.dispatch('/api/books/3')
        mapping.dispatch('/api/books/4')
        mapping.dispatch('/api/books/5')
        mapping.instance_exec(self) do |_|
          _.ok {@urlpath_lru_cache.length} == 3
        end
      end

      spec "[!uqwr7] uses LRU as cache algorithm." do
        |mapping|
        mapping.instance_exec(self) do |_|
          t1 = dispatch('/api/books/1')
          t2 = dispatch('/api/books/2')
          t3 = dispatch('/api/books/3')
          _.ok {@urlpath_lru_cache.values} == [t1, t2, t3]
          t4 = dispatch('/api/books/4')
          _.ok {@urlpath_lru_cache.values} == [t2, t3, t4]
          t5 = dispatch('/api/books/5')
          _.ok {@urlpath_lru_cache.values} == [t3, t4, t5]
          #
          dispatch('/api/books/4')
          _.ok {@urlpath_lru_cache.values} == [t3, t5, t4]
          dispatch('/api/books/3')
          _.ok {@urlpath_lru_cache.values} == [t5, t4, t3]
        end
      end

    end


    topic '#_compile_urlpath_pat()' do

      fixture :proc1 do
        proc {|x| x.to_i }
      end

      fixture :default_patterns do
        |proc1|
        x = K8::DefaultPatterns.new
        x.register('id',   '\d+', &proc1)
        x.register(/_id$/, '\d+', &proc1)
        x
      end

      spec "[!awfgs] returns regexp string, param names, and converter procs." do
        |default_patterns, proc1|
        mapping = K8::ActionMapping.new([], default_patterns: default_patterns)
        mapping.instance_exec(self) do |_|
          #
          actual = _compile_urlpath_pat('/books/{id}')
          _.ok {actual} == ['/books/\d+', ['id'], [proc1]]
          #
          actual = _compile_urlpath_pat('/books/{book_id}/comments/{comment_id}')
          _.ok {actual} == ['/books/\d+/comments/\d+', ['book_id', 'comment_id'], [proc1, proc1]]
          #
          actual = _compile_urlpath_pat('/books/{id:[0-9]+}')
          _.ok {actual} == ['/books/[0-9]+', ['id'], [nil]]
        end
      end

      spec "[!bi7gr] captures urlpath params when 2nd argument is truthy." do
        |default_patterns, proc1|
        mapping = K8::ActionMapping.new([], default_patterns: default_patterns)
        mapping.instance_exec(self) do |_|
          actual = _compile_urlpath_pat('/books/{id}', true)
          _.ok {actual} == ['/books/(\d+)', ['id'], [proc1]]
          #
          actual = _compile_urlpath_pat('/books/{book_id}/comments/{comment_id}', true)
          _.ok {actual} == ['/books/(\d+)/comments/(\d+)', ['book_id', 'comment_id'], [proc1, proc1]]
          #
          actual = _compile_urlpath_pat('/books/{id:[0-9]+}', true)
          _.ok {actual} == ['/books/([0-9]+)', ['id'], [nil]]
        end
      end

      spec "[!mprbx] ex: '/{id:x|y}' -> '/(x|y)', '/{:x|y}' -> '/(?:x|y)'" do
        |default_patterns|
        mapping = K8::ActionMapping.new([], default_patterns: default_patterns)
        mapping.instance_exec(self) do |_|
          _.ok {_compile_urlpath_pat('/item/{key:x|y}', true)}  == ['/item/(x|y)', ['key'], [nil]]
          _.ok {_compile_urlpath_pat('/item/{key:x|y}', false)} == ['/item/(?:x|y)', ['key'], [nil]]
          _.ok {_compile_urlpath_pat('/item/{:x|y}',    true)}  == ['/item/(?:x|y)', [], []]
          _.ok {_compile_urlpath_pat('/item/{:x|y}',    false)} == ['/item/(?:x|y)', [], []]
        end
      end

      spec "[!iln54] param names and conveter procs are nil when no urlpath params." do
        |default_patterns|
        mapping = K8::ActionMapping.new([], default_patterns: default_patterns)
        mapping.instance_exec(self) do |_|
          actual = _compile_urlpath_pat('/books/new')
          _.ok {actual} == ['/books/new', nil, nil]
        end
      end

      spec "[!lhtiz] skips empty param name." do
        |default_patterns, proc1|
        K8::ActionMapping.new([], default_patterns: default_patterns).instance_exec(self) do |_|
          actual = _compile_urlpath_pat('/api/{:\d+}/books')
          _.ok {actual} == ['/api/\d+/books', [], []]
          actual = _compile_urlpath_pat('/api/{:\d+}/books/{id}')
          _.ok {actual} == ['/api/\d+/books/\d+', ['id'], [proc1]]
        end
      end

      spec "[!66zas] skips param name starting with '_'." do
        |default_patterns, proc1|
        K8::ActionMapping.new([], default_patterns: default_patterns).instance_exec(self) do |_|
          actual = _compile_urlpath_pat('/api/{_ver:\d+}/books')
          _.ok {actual} == ['/api/\d+/books', [], []]
          actual = _compile_urlpath_pat('/api/{_ver:\d+}/books/{id}')
          _.ok {actual} == ['/api/\d+/books/\d+', ['id'], [proc1]]
        end
      end

      spec "[!92jcn] '{' and '}' are available in urlpath param pattern." do
        |default_patterns, proc1|
        K8::ActionMapping.new([], default_patterns: default_patterns).instance_exec(self) do |_|
          actual = _compile_urlpath_pat('/blog/{date:\d{4}-\d{2}-\d{2}}')
          _.ok {actual} == ['/blog/\d{4}-\d{2}-\d{2}', ['date'], [nil]]
        end
      end

    end


    topic '#_require_action_class()' do

      spec "[!px9jy] requires file and finds class object." do
        filename = 'test_px9jy.rb'
        content = "class Ex_px9jy < K8::Action; end\n"
        File.open(filename, 'w') {|f| f << content }
        at_end { File.unlink filename }
        K8::ActionMapping.new([]).instance_exec(self) do |_|
          _.ok { _require_action_class './test_px9jy:Ex_px9jy' } == Ex_px9jy
        end
      end

      spec "[!dlcks] don't rescue LoadError when it is not related to argument." do
        filename = 'test_dlcks.rb'
        content = "require 'homhomhom'; class Ex_dlcks < K8::Action; end\n"
        File.open(filename, 'w') {|f| f << content }
        at_end { File.unlink filename }
        K8::ActionMapping.new([]).instance_exec(self) do |_|
          pr = proc { _require_action_class './test_dlcks:Ex_dlcks' }
          _.ok {pr}.raise?(LoadError, "cannot load such file -- homhomhom")
          _.ok {pr.exception.path} == "homhomhom"
        end
      end

      spec "[!mngjz] raises error when failed to load file." do
        filename = 'test_mngjz.rb'
        K8::ActionMapping.new([]).instance_exec(self) do |_|
          pr = proc { _require_action_class './test_mngjz:Ex_mngjz' }
          _.ok {pr}.raise?(LoadError, "'./test_mngjz:Ex_mngjz': cannot load './test_mngjz'.")
        end
      end

      spec "[!8n6pf] class name may have module prefix name." do
        filename = 'test_8n6pf.rb'
        content = "module Ex_8n6pf; class Sample < K8::Action; end; end\n"
        File.open(filename, 'w') {|f| f << content }
        at_end { File.unlink filename }
        K8::ActionMapping.new([]).instance_exec(self) do |_|
          _.ok { _require_action_class './test_8n6pf:Ex_8n6pf::Sample' } == Ex_8n6pf::Sample
        end
      end

      spec "[!6lv7l] raises error when action class not found." do
        filename = 'test_6lv7l.rb'
        content = "module Ex_6lv7l; class Sample_6lv7l < K8::Action; end; end\n"
        File.open(filename, 'w') {|f| f << content }
        at_end { File.unlink filename }
        K8::ActionMapping.new([]).instance_exec(self) do |_|
          pr = proc { _require_action_class './test_6lv7l:Ex_6lv7l::Sample' }
          _.ok {pr}.raise?(NameError, "'./test_6lv7l:Ex_6lv7l::Sample': class not found (Ex_6lv7l::Sample).")
        end
      end

      spec "[!thf7t] raises TypeError when not a class." do
        filename = 'test_thf7t.rb'
        content = "Ex_thf7t = 'XXX'\n"
        File.open(filename, 'w') {|f| f << content }
        at_end { File.unlink filename }
        K8::ActionMapping.new([]).instance_exec(self) do |_|
          pr = proc { _require_action_class './test_thf7t:Ex_thf7t' }
          _.ok {pr}.raise?(TypeError, "'./test_thf7t:Ex_thf7t': class name expected but got \"XXX\".")
        end
      end

      spec "[!yqcgx] raises TypeError when not a subclass of K8::Action." do
        filename = 'test_yqcgx.rb'
        content = "class Ex_yqcgx; end\n"
        File.open(filename, 'w') {|f| f << content }
        at_end { File.unlink filename }
        K8::ActionMapping.new([]).instance_exec(self) do |_|
          pr = proc { _require_action_class './test_yqcgx:Ex_yqcgx' }
          _.ok {pr}.raise?(TypeError, "'./test_yqcgx:Ex_yqcgx': expected subclass of K8::Action but not.")
        end
      end

    end


    topic '#each()' do

      fixture :mapping do
        K8::ActionMapping.new([
            ['/api', [
                ['/books', BooksAction],
                ['/books/{book_id}', BookCommentsAction],
            ]],
        ])
      end

      fixture :expected_tuples do
        [
          ['/api/books/',      BooksAction, {:GET=>:do_index, :POST=>:do_create}],
          ['/api/books/new',   BooksAction, {:GET=>:do_new}],
          ['/api/books/{id}',  BooksAction, {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete}],
          ['/api/books/{id}/edit', BooksAction, {:GET=>:do_edit}],
          ['/api/books/{book_id}/comments',  BookCommentsAction, {:GET=>:do_comments}],
          ['/api/books/{book_id}/comments/{comment_id}',  BookCommentsAction, {:GET=>:do_comment}],
        ]
      end

      spec "[!7ynne] yields each urlpath pattern, action class and action methods." do
        |mapping, expected_tuples|
        arr = []
        mapping.each {|x,y,z| arr << [x, y, z] }
        ok {arr} == expected_tuples
      end

      spec "[!2gwru] returns Enumerator if block is not provided." do
        |mapping, expected_tuples|
        ok {mapping.each}.is_a?(Enumerator)
        ok {mapping.each.map {|x,y,z| [x, y, z] }} == expected_tuples
      end

    end


  end


  topic K8::RackApplication do

    fixture :app do
      K8::RackApplication.new([
          ['/api', [
              ['/books', BooksAction],
          ]],
      ])
    end


    topic '#initialize()' do

      spec "[!vkp65] mounts urlpath mappings." do
        mapping = [
          ['/books'                 , BooksAction],
          ['/books/{id}/comments'   , BookCommentsAction],
        ]
        app = K8::RackApplication.new(mapping)
        expected = <<-'END'
    - urlpath: /books/
      class:   BooksAction
      methods: {GET: do_index, POST: do_create}

    - urlpath: /books/new
      class:   BooksAction
      methods: {GET: do_new}

    - urlpath: /books/{id}
      class:   BooksAction
      methods: {GET: do_show, PUT: do_update, DELETE: do_delete}

    - urlpath: /books/{id}/edit
      class:   BooksAction
      methods: {GET: do_edit}

    - urlpath: /books/{id}/comments/comments
      class:   BookCommentsAction
      methods: {GET: do_comments}

    - urlpath: /books/{id}/comments/comments/{comment_id}
      class:   BookCommentsAction
      methods: {GET: do_comment}

        END
        expected.gsub!(/^    /, '')
        ok {app.show_mappings()} == expected
      end

    end


    topic '#find()' do

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

      spec "[!eb2ms] returns 301 when urlpath not found but found with tailing '/'." do
        |app|
        env = new_env("GET", "/api/books")
        status, headers, body = app.call(env)
        ok {status} == 301
        ok {headers['Location']} == "/api/books/"
        ok {body} == []
      end

      spec "[!02dow] returns 301 when urlpath not found but found without tailing '/'." do
        |app|
        env = new_env("GET", "/api/books/123/")
        status, headers, body = app.call(env)
        ok {status} == 301
        ok {headers['Location']} == "/api/books/123"
        ok {body} == []
      end

      spec "[!2a9c9] adds query string to 'Location' header." do
        |app|
        env = new_env("GET", "/api/books", query: 'x=1&y=2')
        status, headers, body = app.call(env)
        ok {status} == 301
        ok {headers['Location']} == "/api/books/?x=1&y=2"
        #
        env = new_env("GET", "/api/books/123/", query: 'x=3&y=4')
        status, headers, body = app.call(env)
        ok {status} == 301
        ok {headers['Location']} == "/api/books/123?x=3&y=4"
      end

      spec "[!vz07j] redirects only when request method is GET or HEAD." do
        |app|
        env = new_env("HEAD", "/api/books")
        status, headers, body = app.call(env)
        ok {status} == 301
        ok {headers['Location']} == "/api/books/"
        #
        env = new_env("POST", "/api/books")
        status, headers, body = app.call(env)
        ok {status} == 404
        ok {headers['Location']} == nil
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

      spec "[!4vmd3] uses '_method' value of query string as request method when 'POST' method." do
        |app|
        env = new_env("POST", "/api/books/123", query: {"_method"=>"DELETE"})
        app.instance_exec(self) do |_|
          tuple = handle_request(K8::Request.new(env), K8::Response.new)
          status, headers, body = tuple
          _.ok {status}  == 200
          _.ok {body}    == ["<delete:123(Fixnum)>"]  # do_delete() caled
        end
      end

      spec "[!vdllr] clears request and response if possible." do
        |app|
        req  = K8::Request.new(new_env("GET", "/"))
        resp = K8::Response.new()
        req_clear = false
        (class << req; self; end).__send__(:define_method, :clear) { req_clear = true }
        resp_clear = false
        (class << resp; self; end).__send__(:define_method, :clear) { resp_clear = true }
        #
        app.instance_exec(self) do |_|
          tuple = handle_request(req, resp)
          _.ok {req_clear}  == true
          _.ok {resp_clear} == true
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
        yaml_str = <<-'END'
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
        yaml_str.gsub!(/^    /, '')
        ok {app.show_mappings()} == yaml_str
      end

    end


  end


  topic K8::SecretValue do


    topic '#initialize()' do

      spec "[!fbwnh] takes environment variable name." do
        obj = K8::SecretValue.new('DB_PASS')
        ok {obj.name} == 'DB_PASS'
      end

    end


    topic '#value()' do

      spec "[!gg06v] returns environment variable value." do
        obj = K8::SecretValue.new('TEST_HOMHOM')
        ok {obj.value} == nil
        ENV['TEST_HOMHOM'] = 'homhom'
        ok {obj.value} == 'homhom'
      end

    end


    topic '#to_s()' do

      spec "[!7ymqq] returns '<SECRET>' string when name not eixst." do
        ok {K8::SecretValue.new.to_s} == "<SECRET>"
      end

      spec "[!x6edf] returns 'ENV[<name>]' string when name exists." do
        ok {K8::SecretValue.new('DB_PASS').to_s} == "ENV['DB_PASS']"
      end

    end


    topic '#inspect()' do

      spec "[!j27ji] 'inspect()' is alias of 'to_s()'." do
        ok {K8::SecretValue.new('DB_PASS').inspect} == "ENV['DB_PASS']"
      end

    end


    topic '#[](name)' do

      spec "[!jjqmn] creates new instance object with name." do
        obj = K8::SecretValue.new['DB_PASSWORD']
        ok {obj}.is_a?(K8::SecretValue)
        ok {obj.name} == 'DB_PASSWORD'
      end

    end


  end


  topic K8::BaseConfig do


    topic '#initialize()' do

      spec "[!vvd1n] copies key and values from class object." do
        class C01 < K8::BaseConfig
          add :haruhi  , 'C'   , "Suzumiya"
          add :mikuru  , 'E'   , "Asahina"
          add :yuki    , 'A'   , "Nagato"
        end
        c = C01.new
        c.instance_exec(self) do |_|
          _.ok {@haruhi} == 'C'
          _.ok {@mikuru} == 'E'
          _.ok {@yuki}   == 'A'
        end
      end

      spec "[!6dilv] freezes self and class object if 'freeze:' is true." do
        class C02 < K8::BaseConfig
          add :haruhi  , 'C'   , "Suzumiya"
          add :mikuru  , 'E'   , "Asahina"
          add :yuki    , 'A'   , "Nagato"
        end
        ## when freeze: false
        c = C02.new(freeze: false)
        pr = proc { c.instance_variable_set('@yuki', 'B') }
        ok {pr}.NOT.raise?(Exception)
        pr = proc { C02.class_eval { put :yuki, 'B' } }
        ok {pr}.NOT.raise?(Exception)
        ## when freeze: true
        c = C02.new
        pr = proc { c.instance_variable_set('@yuki', 'B') }
        ok {pr}.raise?(RuntimeError, "can't modify frozen C02")
        pr = proc { C02.class_eval { put :yuki, 'B' } }
        ok {pr}.raise?(RuntimeError, "can't modify frozen class")
      end

      case_when "[!xok12] when value is SECRET..." do

        spec "[!a4a4p] raises error when key not specified." do
          class C03 < K8::BaseConfig
            add :db_pass    , SECRET,   "db password"
          end
          pr = proc { C03.new }
          ok {pr}.raise?(K8::ConfigError, "config 'db_pass' should be set, but not.")
        end

        spec "[!w4yl7] raises error when ENV value not specified." do
          class C04 < K8::BaseConfig
            add :db_pass1    , SECRET['DB_PASS1'],   "db password"
          end
          ok {ENV['DB_PASS1']} == nil
          pr = proc { C04.new }
          ok {pr}.raise?(K8::ConfigError, )
        end

        spec "[!he20d] get value from ENV." do
          class C05 < K8::BaseConfig
            add :db_pass1    , SECRET['DB_PASS1'],   "db password"
          end
          begin
            ENV['DB_PASS1'] = 'homhom'
            pr = proc { C05.new }
            ok {pr}.NOT.raise?(Exception)
            ok {C05.new.db_pass1} == 'homhom'
          ensure
            ENV['DB_PASS1'] = nil
          end
        end

      end

    end


    topic '.has?()' do

      spec "[!dv87n] returns true iff key is set." do
        class C11 < K8::BaseConfig
          @result1 = has? :foo
          put :foo, 1
          @result2 = has? :foo
        end
        ok {C11.instance_variable_get('@result1')} == false
        ok {C11.instance_variable_get('@result2')} == true
      end

    end


    topic '.put()' do

      spec "[!h9b47] defines getter method." do
        class C21 < K8::BaseConfig
          put :hom, 123, "HomHom"
        end
        ok {C21.instance_methods}.include?(:hom)
        ok {C21.new.hom} == 123
      end

      spec "[!ncwzt] stores key with value, description and secret flag." do
        class C22 < K8::BaseConfig
          put :hom,  123,    "HomHom"
          put :hom2, SECRET, "Secret HomHom"
        end
        ok {C22.instance_variable_get('@__all')} == {
          :hom  => [123, "HomHom", false],
          :hom2 => [K8::BaseConfig::SECRET, "Secret HomHom", true],
        }
      end

      spec "[!mun1v] keeps secret flag." do
        class C23 < K8::BaseConfig
          put :haruhi  , 'C'   , "Suzumiya"
          put :mikuru  , SECRET, "Asahina"
          put :yuki    , SECRET, "Nagato"
        end
        class C23
          put :mikuru  , 'F'
        end
        ok {C23.instance_variable_get('@__all')} == {
          :haruhi => ['C', "Suzumiya", false],
          :mikuru => ['F', "Asahina", true],
          :yuki   => [K8::BaseConfig::SECRET, "Nagato", true],
        }
      end

    end


    topic '.add()' do

      spec "[!envke] raises error when already added." do
        class C31 < K8::BaseConfig
          add :hom, 123, "HomHom"
          @ex = nil
          begin
            add :hom, 456, "HomHom"
          rescue => ex
            @ex = ex
          end
        end
        ex = C31.instance_variable_get('@ex')
        ok {ex} != nil
        ok {ex}.is_a?(K8::ConfigError)
        ok {ex.message} == "add(:hom, 456): cannot add because already added; use set() or put() instead."
      end

      spec "[!6cmb4] adds new key, value and desc." do
        class C32 < K8::BaseConfig
          add :hom, 123, "HomHom"
          add :hom2, 'HOM'
        end
        all = C32.instance_variable_get('@__all')
        ok {all} == {:hom=>[123, "HomHom", false], :hom2=>['HOM', nil, false]}
      end

    end


    topic '.set()' do

      spec "[!2yis0] raises error when not added yet." do
        class C41 < K8::BaseConfig
          @ex = nil
          begin
            set :hom, 123, "HomHom"
          rescue => ex
            @ex = ex
          end
        end
        ex = C41.instance_variable_get('@ex')
        ok {ex} != nil
        ok {ex}.is_a?(K8::ConfigError)
        ok {ex.message} == "set(:hom, 123): cannot set because not added yet; use add() or put() instead."
      end

      spec "[!3060g] sets key, value and desc." do
        class C42 < K8::BaseConfig
          add :hom, 123, "HomHom"
        end
        class C42
          set :hom, 456
        end
        all = C42.instance_variable_get('@__all')
        ok {all} == {:hom=>[456, "HomHom", false]}
      end

    end


    topic '.each()' do

      spec "[!iu88i] yields with key, value, desc and secret flag." do
        class C51 < K8::BaseConfig
          add :haruhi  , 'C'   , "Suzumiya"
          add :mikuru  , SECRET, "Asahina"
          add :yuki    , 'A'   , "Nagato"
        end
        class C51
          set :mikuru  , 'F'
          add :sasaki  , 'B'
        end
        #
        arr = []
        C51.each {|*args| arr << args }
        ok {arr} == [
          [:haruhi, 'C', "Suzumiya", false],
          [:mikuru, 'F', "Asahina", true],
          [:yuki,   'A', "Nagato", false],
          [:sasaki, 'B', nil, false],
        ]
      end

    end


    topic '.get()' do

      spec "[!zlhnp] returns value corresponding to key." do
        class C61 < K8::BaseConfig
          add :haruhi  , 'C'   , "Suzumiya"
          add :mikuru  , 'E'   , "Asahina"
          add :yuki    , 'A'   , "Nagato"
        end
        class C61
          set :mikuru  , 'F'
          add :sasaki  , 'B'
        end
        ok {C61.get(:haruhi)} == 'C'
        ok {C61.get(:mikuru)} == 'F'
        ok {C61.get(:yuki)}   == 'A'
        ok {C61.get(:sasaki)} == 'B'
      end

      spec "[!o0k05] returns default value (=nil) when key is not added." do
        class C62 < K8::BaseConfig
          add :haruhi  , 'C'   , "Suzumiya"
          add :mikuru  , 'E'   , "Asahina"
          add :yuki    , 'A'   , "Nagato"
        end
        ok {C62.get(:sasaki)}     == nil
        ok {C62.get(:sasaki, "")} == ""
      end

    end


    topic '[](key)' do

      spec "[!jn9l5] returns value corresponding to key." do
        class C71 < K8::BaseConfig
          add :haruhi  , 'C'   , "Suzumiya"
          add :mikuru  , 'E'   , "Asahina"
          add :yuki    , 'A'   , "Nagato"
        end
        class C71
          set :mikuru  , 'F'
          add :sasaki  , 'B'
        end
        c = C71.new
        ok {c[:haruhi]} == 'C'
        ok {c[:mikuru]} == 'F'
        ok {c[:yuki]}   == 'A'
        ok {c[:sasaki]} == 'B'
      end

    end


    topic '#get_all()' do

      spec "[!4ik3c] returns all keys and values which keys start with prefix as hash object." do
        class C81 < K8::BaseConfig
          add :session_cookie_name     , 'rack.sess'
          add :session_cookie_expires  , 30*60*60
          add :session_cookie_secure   , true
          add :name    , 'Homhom'
          add :secure  , false
        end
        #
        c = C81.new
        ok {c.get_all(:session_cookie_)} == {
          :name     => 'rack.sess',
          :expires  => 30*60*60,
          :secure   => true,
        }
      end

    end


  end


end


if __FILE__ == $0
  Oktest::main()
end
