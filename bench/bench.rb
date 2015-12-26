# -*- coding: utf-8 -*-

def detect_flag(cmdopt)
  if cmdopt == '0'
    return false
  end
  begin
    result = yield
    return !!result
  rescue LoadError
    if cmdopt.to_s.empty?
      return false
    else
      raise
    end
  end
end

$LOAD_PATH << '.'

flag_rack = detect_flag($rack) { require 'rack'            ; defined?(Rack) }
flag_sina = detect_flag($sina) { require 'sinatra/base'    ; defined?(Sinatra) }
flag_mplx = detect_flag($mplx) { require 'rack-multiplexer'; defined?(Rack::Multiplexer) }
flag_k8   = detect_flag($k8  ) { require 'keight'          ; defined?(K8) }
flag_jet  = detect_flag($jet ) { require 'rack-jet_router' ; defined?(Rack::JetRouter) }


if flag_rack

  class RackApp1
    def call(env)
      [200, {"Content-Type"=>"text/html"}, ["<h1>hello</h1>"]]
    end
  end

  class RackApp2
    def call(env)
      req  = Rack::Request.new(env)
      [200, {"Content-Type"=>"text/html"}, ["<h1>hello</h1>"]]
    end
  end

  class RackApp3
    def call(env)
      resp = Rack::Response.new
      #[resp.status, resp.headers, ["<h1>hello</h1>"]]
      [200, {"Content-Type"=>"text/html"}, ["<h1>hello</h1>"]]
    end
  end

  class RackApp4
    def call(env)
      req  = Rack::Request.new(env)
      resp = Rack::Response.new
      #[resp.status, resp.headers, ["<h1>hello</h1>"]]
      [200, {"Content-Type"=>"text/html"}, ["<h1>hello</h1>"]]
    end
  end

  rack_app1 = RackApp1.new
  rack_app2 = RackApp2.new
  rack_app3 = RackApp3.new
  rack_app4 = RackApp4.new

end


$api_entries   = %w[books authors account orders ranking about news support]
$admin_entries = ('a'..'z').each_with_index.collect {|c,i| "%s%02d" % [c*3, i+1] }


if flag_sina

  class SinaApp < Sinatra::Base

    set :sessions   , false
    set :logging    , false
    set :protection , false
    set :x_cascade  , false

    for x in $api_entries
      get    "/api/#{x}"          do "<h1>index</h1>"  end
      post   "/api/#{x}"          do "<h1>create</h1>" end
      #get    "/api/#{x}/new"      do "<h1>new</h1>"    end
      get    "/api/#{x}/:id"      do "<h1>show</h1>"   end
      put    "/api/#{x}/:id"      do "<h1>update</h1>" end
      delete "/api/#{x}/:id"      do "<h1>delete</h1>" end
      #get    "/api/#{x}/:id/edit" do "<h1>edit</h1>"   end
    end

    for x in $admin_entries   # 'aaa01', 'bbb02', ..., 'zzz26'
      get    "/admin/#{x}"        do '<p>index</p>'    end
      post   "/admin/#{x}"        do '<p>create</p>'   end
      get    "/admin/#{x}/:id"    do '<p>show</p>'     end
      put    "/admin/#{x}/:id"    do '<p>update</p>'   end
      delete "/admin/#{x}/:id"    do '<p>delete</p>'   end
    end

  end

  sina_app = SinaApp.new

end


if flag_mplx

  mplx_app1 = proc {
    #
    proc_ = proc {|env|
      [200, {"Content-Type"=>"text/html"}, ["<h1>hello</h1>"]]
      #req  = Rack::Request.new(env)
      #resp = Rack::Response.new
      #[resp.status, resp.headers, ["<h1>index</h1>"]]
    }
    #
    app = Rack::Multiplexer.new
    for x in $api_entries
      app.get    "/api/#{x}",           proc_
      app.post   "/api/#{x}",           proc_
      #app.get    "/api/#{x}/new",       proc_
      app.get    "/api/#{x}/:id",       proc_
      app.post   "/api/#{x}/:id",       proc_
      app.delete "/api/#{x}/:id",       proc_
      #app.get    "/api/#{x}/:id/edit",  proc_
    end
    for x in $admin_entries   # 'aaa01', 'bbb02', ..., 'zzz26'
      app.get    "/admin/#{x}",         proc_
      app.post   "/admin/#{x}",         proc_
      app.get    "/admin/#{x}/:id",     proc_
      app.put    "/admin/#{x}/:id",     proc_
      app.delete "/admin/#{x}/:id",     proc_
    end
    #
    app
  }.call()

  mplx_app2 = proc {
    #
    proc_ = proc {|env|
      [200, {"Content-Type"=>"text/html"}, ["<h1>hello</h1>"]]
    }
    #
    api = Rack::Multiplexer.new
    for x in $api_entries
      api.get    "/api/#{x}",       proc_
      api.post   "/api/#{x}",       proc_
      #api.get    "/api/#{x}/new",   proc_
      api.get    "/api/#{x}/:id",   proc_
      api.post   "/api/#{x}/:id",   proc_
      api.delete "/api/#{x}/:id",   proc_
      #api.get    "/api/#{x}/:id/edit",  proc_
    end
    #
    admin = Rack::Multiplexer.new
    for x in $admin_entries   # 'aaa01', 'bbb02', ..., 'zzz26'
      admin.get    "/admin/#{x}",      proc_
      admin.post   "/admin/#{x}",      proc_
      admin.get    "/admin/#{x}/:id",  proc_
      admin.put    "/admin/#{x}/:id",  proc_
      admin.delete "/admin/#{x}/:id",  proc_
    end
    #
    app = proc {|env|
      urlpath = env['PATH_INFO']
      if urlpath.start_with?('/api')
        api.call(env)
      elsif urlpath.start_with?('/admin')
        admin.call(env)
      else
        [404, {}, []]
      end
    }
    #
    app
  }.call()

end


if flag_k8

  class DummyAction < K8::Action
    mapping '',       :GET=>:do_index, :POST=>:do_create
    #mapping '/new',   :GET=>:do_new
    mapping '/{id}',  :GET=>:do_show, :PUT=>:do_edit, :DELETE=>:do_delete
    #mapping '/{id}/edit', :GET=>:do_edit
    def do_index        ; "<h1>index</h1>"; end
    def do_create       ; "<h1>create</h1>"; end
    def do_new          ; "<h1>new</h1>"; end
    def do_show(id)     ; "<h1>show</h1>"; end
    def do_update(id)   ; "<h1>update</h1>"; end
    def do_delete(id)   ; "<h1>delete</h1>"; end
    def do_edit(id)     ; "<h1>edit</h1>"; end
  end
  #
  k8_app = proc {
    mapping = [
      ['/api', [
        ['/books',   DummyAction],
        ['/books/{id}/comments', DummyAction],
        ['/authors', DummyAction],
        ['/authors/{id}/comments', DummyAction],
        ['/account', DummyAction],
        ['/orders',  DummyAction],
        ['/ranking', DummyAction],
        ['/about',   DummyAction],
        ['/news',    DummyAction],
        ['/support', DummyAction],
      ]],
      ['/admin', $admin_entries.collect {|x|  # 'aaa01', 'bbb02', ..., 'zzz26'
        ["/#{x}", DummyAction]
      }],
    ]
    opts = {
      urlpath_cache_size: 0,
      enable_urlpath_param_range: ENV['K8RANGE'] != '0',
    }
    K8::RackApplication.new(mapping, opts)
  }.call()

end


if flag_jet

  jet_app = proc {
    #
    jet_proc = proc {|env|
      [200, {"Content-Type"=>"text/html"}, ["<h1>hello</h1>"]]
      #req  = Rack::Request.new(env)
      #resp = Rack::Response.new
      #[resp.status, resp.headers, ["<h1>index</h1>"]]
    }
    methods1 = {:GET=>jet_proc, :POST=>jet_proc}
    methods2 = {:GET=>jet_proc, :PUT=>jet_proc, :DELETE=>jet_proc}
    #
    jet_mapping = [
        ['/api', [
            ['/books',           [ ['', methods1], ['/:id', methods2] ] ],
            ['/books/:book_id/comments',    [ ['', methods1], ['/:id', methods2] ] ],
            ['/authors',         [ ['', methods1], ['/:id', methods2] ] ],
            ['/authors/author_id/comments', [ ['', methods1], ['/:id', methods2] ] ],
            ['/account',         [ ['', methods1], ['/:id', methods2] ] ],
            ['/orders',          [ ['', methods1], ['/:id', methods2] ] ],
            ['/ranking',         [ ['', methods1], ['/:id', methods2] ] ],
            ['/about',           [ ['', methods1], ['/:id', methods2] ] ],
            ['/news',            [ ['', methods1], ['/:id', methods2] ] ],
            ['/support',         [ ['', methods1], ['/:id', methods2] ] ],
        ]],
        ['/admin', $admin_entries.each_with_object([]) {|x, arr|
            arr << ["/#{x}",      methods1]
            arr << ["/#{x}/:id",  methods2]
        }]
    ]
    #
    jet_opts = {
      urlpath_cache_size: 0,
    }
    #
    Rack::JetRouter.new(jet_mapping, jet_opts)
  }.call()

end


def _chk(tuple)
  tuple[0] == 200  or raise "200 expected but got #{tuple[0]}"
  GC.start
end

require 'rack' unless defined?(Rack)
$environ = Rack::MockRequest.env_for("http://localhost/", method: 'GET')

def newenv(path)
  env = $environ.dup
  env['PATH_INFO'] = path
  env
end


require 'benchmarker'

N = ($N || 100000).to_i

Benchmarker.new(:width=>30, :loop=>N) do |bm|

  urlpaths = %w[/api/books /api/books/123 /api/support /api/support/123
                /admin/aaa01 /admin/aaa01/123 /admin/zzz26 /admin/zzz26/123]


  tuple = nil


  ### empty task

  bm.empty_task do
    newenv("/api/hello")
  end


  ### Rack
  if flag_rack
    rack_apps = [rack_app1, rack_app2, rack_app3, rack_app4]
    for rack_app, i in rack_apps.each_with_index
      bm.task("(Rack#{i+1}) /some/where") do
        tuple = rack_app.call(newenv("/some/where"))
      end
      _chk(tuple)
    end
  end


  ### Sinatra
  if flag_sina
    for upath in urlpaths
      bm.task("(Sina) #{upath}") do
        tuple = sina_app.call(newenv(upath))
      end
      _chk(tuple)
    end
  end


  ### Rack::Multiplexer
  if flag_mplx
    for upath in urlpaths
      bm.task("(Mplx) #{upath}") do
        tuple = mplx_app1.call(newenv(upath))
      end
      _chk(tuple)
    end
  end

  if flag_mplx
    for upath in urlpaths
      bm.task("(Mplx') #{upath}") do
        tuple = mplx_app2.call(newenv(upath))
      end
      _chk(tuple)
    end
  end


  ### Keight

  if flag_k8
    for upath in urlpaths
      bm.task("(K8) #{upath}") do
        tuple = k8_app.call(newenv(upath))
      end
      _chk(tuple)
    end
  end


  ### Rack::JetRouter

  if flag_jet
    for upath in urlpaths
      bm.task("(JetR) #{upath}") do
        tuple = jet_app.call(newenv(upath))
      end
      _chk(tuple)
    end
  end

end
