# -*- coding: utf-8 -*-

$LOAD_PATH << '.'

require 'rack'
require 'sinatra/base'     rescue nil
require 'rack-multiplexer' rescue nil
require 'keight'           rescue nil


if defined?(Rack)

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


if defined?(Sinatra)

  class SinaApp < Sinatra::Base

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


if defined?(Rack::Multiplexer)

  mplx_dummy = proc {|env|
    [200, {"Content-Type"=>"text/html"}, ["<h1>hello</h1>"]]
    #req  = Rack::Request.new(env)
    #resp = Rack::Response.new
    #[resp.status, resp.headers, ["<h1>index</h1>"]]
  }

  mplx_app1 = Rack::Multiplexer.new

  for x in $api_entries
    mplx_app1.get    "/api/#{x}",           mplx_dummy
    mplx_app1.post   "/api/#{x}",           mplx_dummy
    #mplx_app1.get    "/api/#{x}/new",       mplx_dummy
    mplx_app1.get    "/api/#{x}/:id",       mplx_dummy
    mplx_app1.post   "/api/#{x}/:id",       mplx_dummy
    mplx_app1.delete "/api/#{x}/:id",       mplx_dummy
    #mplx_app1.get    "/api/#{x}/:id/edit",  mplx_dummy
  end
  for x in $admin_entries   # 'aaa01', 'bbb02', ..., 'zzz26'
    mplx_app1.get    "/admin/#{x}",         mplx_dummy
    mplx_app1.post   "/admin/#{x}",         mplx_dummy
    mplx_app1.get    "/admin/#{x}/:id",     mplx_dummy
    mplx_app1.put    "/admin/#{x}/:id",     mplx_dummy
    mplx_app1.delete "/admin/#{x}/:id",     mplx_dummy
  end

  mplx_api = Rack::Multiplexer.new
  for x in $api_entries
    mplx_api.get    "/api/#{x}",           mplx_dummy
    mplx_api.post   "/api/#{x}",           mplx_dummy
   #mplx_api.get    "/api/#{x}/new",       mplx_dummy
    mplx_api.get    "/api/#{x}/:id",       mplx_dummy
    mplx_api.post   "/api/#{x}/:id",       mplx_dummy
    mplx_api.delete "/api/#{x}/:id",       mplx_dummy
   #mplx_api.get    "/api/#{x}/:id/edit",  mplx_dummy
  end
  mplx_admin = Rack::Multiplexer.new
  for x in $admin_entries   # 'aaa01', 'bbb02', ..., 'zzz26'
    mplx_admin.get    "/admin/#{x}",         mplx_dummy
    mplx_admin.post   "/admin/#{x}",         mplx_dummy
    mplx_admin.get    "/admin/#{x}/:id",     mplx_dummy
    mplx_admin.put    "/admin/#{x}/:id",     mplx_dummy
    mplx_admin.delete "/admin/#{x}/:id",     mplx_dummy
  end
  mplx_app2 = proc {|env|
    urlpath = env['PATH_INFO']
    if urlpath.start_with?('/api')
      mplx_api.call(env)
    elsif urlpath.start_with?('/admin')
      mplx_admin.call(env)
    else
      [404, {}, []]
    end
  }

end


if defined?(K8)

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
  k8_app_opts = {urlpath_cache_size: 0}
  k8_app = K8::RackApplication.new(k8_app_opts)
  k8_app.mount '/api', [
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
  ]
  pairs = $admin_entries.collect {|x|  # 'aaa01', 'bbb02', ..., 'zzz26'
    ["/#{x}", DummyAction]
  }
  k8_app.mount '/admin', pairs
  #
  k8_app.find('/')     # warm up

end


def _chk(tuple)
  tuple[0] == 200  or raise "200 expected but got #{tuple[0]}"
  GC.start
end

$environ = Rack::MockRequest.env_for("http://localhost/")
$environ['REQUEST_METHOD'] = 'GET'

def newenv(path)
  env = $environ.dup
  env['PATH_INFO'] = path
  env
end


require 'benchmarker'


Benchmarker.new(:width=>30, :loop=>100000) do |bm|

  flag_rack = flag_sinatra = flag_multiplexer = flag_keight = false
  flag_rack        = defined?(Rack)
  #flag_sinatra     = defined?(Sinatra)
  flag_multiplexer = defined?(Rack::Multiplexer)
  flag_keight      = defined?(K8)

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
  if flag_sinatra
    for upath in urlpaths
      bm.task("(Sina) #{upath}") do
        tuple = sina_app.call(newenv(upath))
      end
      _chk(tuple)
    end
  end


  ### Rack::Multiplexer
  if flag_multiplexer
    for upath in urlpaths
      bm.task("(Mplx) #{upath}") do
        tuple = mplx_app1.call(newenv(upath))
      end
      _chk(tuple)
    end
  end

  if flag_multiplexer
    for upath in urlpaths
      bm.task("(Mplx') #{upath}") do
        tuple = mplx_app2.call(newenv(upath))
      end
      _chk(tuple)
    end
  end


  ### Keight

  if flag_keight
    for upath in urlpaths
      bm.task("(K8) #{upath}") do
        tuple = k8_app.call(newenv(upath))
      end
      _chk(tuple)
    end
  end

end
