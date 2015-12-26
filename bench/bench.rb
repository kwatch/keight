# -*- coding: utf-8 -*-

$LOAD_PATH << '.'

def _version(cmdopt)
  if cmdopt == '0'
    return nil
  end
  begin
    return yield
  rescue LoadError
    if cmdopt.to_s.empty?
      return nil
    else
      raise
    end
  end
end

version_rack = _version($rack) { require 'rack'            ; Rack.release }
version_sina = _version($sina) { require 'sinatra/base'    ; Sinatra::VERSION }
version_mplx = _version($mplx) { require 'rack/multiplexer'; Rack::Multiplexer::VERSION }
version_k8   = _version($k8  ) { require 'keight'          ; K8::RELEASE }
version_jet  = _version($jet ) { require 'rack/jet_router' ; Rack::JetRouter::RELEASE }

$api_entries = ('a'..'z').each_with_index.map {|x, i| "%s%02d" % [x*3, i+1] }


if version_rack

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


if version_sina

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

  end

  sina_app = SinaApp.new

end


if version_mplx

  mplx_app = proc {
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
    #
    app
  }.call()

end


if version_k8

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
      ['/api', $api_entries.map {|x| ["/#{x}", DummyAction] }],
    ]
    opts = {
      urlpath_cache_size: ($k8size || 0).to_i,
      enable_urlpath_param_range: $k8range != '0',
    }
    K8::RackApplication.new(mapping, opts)
  }.call()

end


if version_jet

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
    arr = $api_entries.map {|x| ["/#{x}", [['', methods1], ['/:id', methods2]]] }
    jet_mapping = [
        ['/api', $api_entries.map {|x| ["/#{x}", [
                                           ['',     methods1],
                                           ['/:id', methods2],
                                       ]] }
        ],
    ]
    #
    jet_opts = {
      urlpath_cache_size: ($jetcache || 0).to_i,
      enable_urlpath_param_range: $jetrange != '0',
    }
    #
    Rack::JetRouter.new(jet_mapping, jet_opts)
  }.call()

end


def _chk(tuple)
  tuple[0] == 200  or raise "200 expected but got #{tuple[0]}"
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

  urlpaths = [
    '/api/aaa01',
    '/api/aaa01/123',
    '/api/zzz26',
    '/api/zzz26/789',
  ]

  tuple = nil

  puts ""
  puts "** rack            : #{version_rack || '-'}"
  puts "** rack-jet_router : #{version_jet  || '-'}"
  puts "** rack-multiplexer: #{version_mplx || '-'}"
  puts "** sinatra         : #{version_sina || '-'}"
  puts "** keight          : #{version_k8   || '-'}"
  puts ""
  puts "** N=#{N}"

  ### empty task

  bm.empty_task do
    newenv("/api/hello")
  end


  ### Rack
  if version_rack
    rack_labels = ['Rack', 'R:Rq', 'R:Rs', 'RqRs']
    rack_apps = [rack_app1, rack_app2, rack_app3, rack_app4]
    for rack_app, label in rack_apps.zip(rack_labels)
      bm.task("(#{label}) /some/where") do
        tuple = rack_app.call(newenv("/some/where"))
      end
      _chk(tuple)
    end
  end


  ### Sinatra
  if version_sina
    for upath in urlpaths
      bm.task("(Sina) #{upath}") do
        tuple = sina_app.call(newenv(upath))
      end
      _chk(tuple)
    end
  end


  ### Rack::Multiplexer
  if version_mplx
    for upath in urlpaths
      bm.task("(Mplx) #{upath}") do
        tuple = mplx_app.call(newenv(upath))
      end
      _chk(tuple)
    end
  end


  ### Keight

  if version_k8
    for upath in urlpaths
      bm.task("(K8  ) #{upath}") do
        tuple = k8_app.call(newenv(upath))
      end
      _chk(tuple)
    end
  end


  ### Rack::JetRouter

  if version_jet
    for upath in urlpaths
      bm.task("(JetR) #{upath}") do
        tuple = jet_app.call(newenv(upath))
      end
      _chk(tuple)
    end
  end

end
