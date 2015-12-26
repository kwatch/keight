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


__END__

###
### Example result
###

$ ruby -I../lib -I. -s bench.rb -N=1000000

benchmarker.rb:   release 0.0.0
RUBY_VERSION:     2.3.0
RUBY_PATCHLEVEL:  0
RUBY_PLATFORM:    x86_64-darwin15

** rack            : 1.6.4
** rack-jet_router : 1.1.0
** rack-multiplexer: 0.0.8
** sinatra         : 1.4.6
** keight          : 0.2.0

** N=1000000

##                                  user       sys     total      real
(Empty)                           7.3000    0.0900    7.3900    7.4131
(Rack) /some/where                0.8400   -0.0400    0.8000    0.7903
(R:Rq) /some/where                0.8400   -0.0500    0.7900    0.7743
(R:Rs) /some/where                6.1600   -0.0500    6.1100    6.0898
(RqRs) /some/where                6.4200   -0.0600    6.3600    6.3407
(Sina) /api/aaa01                84.5700   18.0800  102.6500  102.7069
(Sina) /api/aaa01/123            94.1300   18.4800  112.6100  112.6892
(Sina) /api/zzz26               125.7300   19.0800  144.8100  145.0454
(Sina) /api/zzz26/789           133.8000   18.9600  152.7600  152.9070
(Mplx) /api/aaa01                 5.0200    0.1700    5.1900    5.1821
(Mplx) /api/aaa01/123            16.7100    0.3100   17.0200   17.0086
(Mplx) /api/zzz26                23.3700   -0.0400   23.3300   23.3190
(Mplx) /api/zzz26/789            35.6500    0.0100   35.6600   35.6661
(K8  ) /api/aaa01                 5.9200    0.0300    5.9500    5.9423
(K8  ) /api/aaa01/123             9.2200    0.0900    9.3100    9.2934
(K8  ) /api/zzz26                 6.2700    0.0600    6.3300    6.3158
(K8  ) /api/zzz26/789            10.0300    0.1300   10.1600   10.1547
(JetR) /api/aaa01                 1.1800    0.0400    1.2200    1.2154
(JetR) /api/aaa01/123             5.0400    0.1100    5.1500    5.1431
(JetR) /api/zzz26                 0.9600    0.0300    0.9900    0.9681
(JetR) /api/zzz26/789             5.6900    0.1100    5.8000    5.7946

## Ranking                          real
(R:Rq) /some/where                0.7743 (100.0%) ********************
(Rack) /some/where                0.7903 ( 98.0%) ********************
(JetR) /api/zzz26                 0.9681 ( 80.0%) ****************
(JetR) /api/aaa01                 1.2154 ( 63.7%) *************
(JetR) /api/aaa01/123             5.1431 ( 15.1%) ***
(Mplx) /api/aaa01                 5.1821 ( 14.9%) ***
(JetR) /api/zzz26/789             5.7946 ( 13.4%) ***
(K8  ) /api/aaa01                 5.9423 ( 13.0%) ***
(R:Rs) /some/where                6.0898 ( 12.7%) ***
(K8  ) /api/zzz26                 6.3158 ( 12.3%) **
(RqRs) /some/where                6.3407 ( 12.2%) **
(K8  ) /api/aaa01/123             9.2934 (  8.3%) **
(K8  ) /api/zzz26/789            10.1547 (  7.6%) **
(Mplx) /api/aaa01/123            17.0086 (  4.6%) *
(Mplx) /api/zzz26                23.3190 (  3.3%) *
(Mplx) /api/zzz26/789            35.6661 (  2.2%)
(Sina) /api/aaa01               102.7069 (  0.8%)
(Sina) /api/aaa01/123           112.6892 (  0.7%)
(Sina) /api/zzz26               145.0454 (  0.5%)
(Sina) /api/zzz26/789           152.9070 (  0.5%)

## Matrix                           real     [01]     [02]     [03]     [04]     [05]     [06]     [07]     [08]     [09]     [10]     [11]     [12]     [13]     [14]     [15]     [16]     [17]     [18]     [19]     [20]
[01] (Rack2) /some/where          0.7743   100.0%   102.1%   125.0%   157.0%   664.2%   669.2%   748.3%   767.4%   786.5%   815.6%   818.9%  1200.2%  1311.4%  2196.6%  3011.5%  4606.1% 13264.0% 14553.1% 18731.7% 19747.0%
[02] (Rack1) /some/where          0.7903    98.0%   100.0%   122.5%   153.8%   650.7%   655.7%   733.2%   751.9%   770.5%   799.1%   802.3%  1175.9%  1284.8%  2152.1%  2950.5%  4512.7% 12995.2% 14258.3% 18352.2% 19346.9%
[03] (JetR) /api/zzz26            0.9681    80.0%    81.6%   100.0%   125.5%   531.2%   535.3%   598.5%   613.8%   629.0%   652.4%   654.9%   959.9%  1048.9%  1756.9%  2408.7%  3684.0% 10608.8% 11639.9% 14982.1% 15794.1%
[04] (JetR) /api/aaa01            1.2154    63.7%    65.0%    79.7%   100.0%   423.2%   426.4%   476.8%   488.9%   501.0%   519.6%   521.7%   764.6%   835.5%  1399.4%  1918.6%  2934.5%  8450.4%  9271.7% 11933.8% 12580.6%
[05] (JetR) /api/aaa01/123        5.1431    15.1%    15.4%    18.8%    23.6%   100.0%   100.8%   112.7%   115.5%   118.4%   122.8%   123.3%   180.7%   197.4%   330.7%   453.4%   693.5%  1997.0%  2191.1%  2820.2%  2973.1%
[06] (Mplx) /api/aaa01            5.1821    14.9%    15.3%    18.7%    23.5%    99.2%   100.0%   111.8%   114.7%   117.5%   121.9%   122.4%   179.3%   196.0%   328.2%   450.0%   688.3%  1982.0%  2174.6%  2799.0%  2950.7%
[07] (JetR) /api/zzz26/789        5.7946    13.4%    13.6%    16.7%    21.0%    88.8%    89.4%   100.0%   102.5%   105.1%   109.0%   109.4%   160.4%   175.2%   293.5%   402.4%   615.5%  1772.5%  1944.7%  2503.1%  2638.8%
[08] (K8) /api/aaa01              5.9423    13.0%    13.3%    16.3%    20.5%    86.6%    87.2%    97.5%   100.0%   102.5%   106.3%   106.7%   156.4%   170.9%   286.2%   392.4%   600.2%  1728.4%  1896.4%  2440.9%  2573.2%
[09] (Rack3) /some/where          6.0898    12.7%    13.0%    15.9%    20.0%    84.5%    85.1%    95.2%    97.6%   100.0%   103.7%   104.1%   152.6%   166.7%   279.3%   382.9%   585.7%  1686.5%  1850.5%  2381.8%  2510.9%
[10] (K8) /api/zzz26              6.3158    12.3%    12.5%    15.3%    19.2%    81.4%    82.0%    91.7%    94.1%    96.4%   100.0%   100.4%   147.1%   160.8%   269.3%   369.2%   564.7%  1626.2%  1784.3%  2296.6%  2421.0%
[11] (Rack4) /some/where          6.3407    12.2%    12.5%    15.3%    19.2%    81.1%    81.7%    91.4%    93.7%    96.0%    99.6%   100.0%   146.6%   160.2%   268.2%   367.8%   562.5%  1619.8%  1777.2%  2287.5%  2411.5%
[12] (K8) /api/aaa01/123          9.2934     8.3%     8.5%    10.4%    13.1%    55.3%    55.8%    62.4%    63.9%    65.5%    68.0%    68.2%   100.0%   109.3%   183.0%   250.9%   383.8%  1105.2%  1212.6%  1560.7%  1645.3%
[13] (K8) /api/zzz26/789         10.1547     7.6%     7.8%     9.5%    12.0%    50.6%    51.0%    57.1%    58.5%    60.0%    62.2%    62.4%    91.5%   100.0%   167.5%   229.6%   351.2%  1011.4%  1109.7%  1428.4%  1505.8%
[14] (Mplx) /api/aaa01/123       17.0086     4.6%     4.6%     5.7%     7.1%    30.2%    30.5%    34.1%    34.9%    35.8%    37.1%    37.3%    54.6%    59.7%   100.0%   137.1%   209.7%   603.9%   662.5%   852.8%   899.0%
[15] (Mplx) /api/zzz26           23.3190     3.3%     3.4%     4.2%     5.2%    22.1%    22.2%    24.8%    25.5%    26.1%    27.1%    27.2%    39.9%    43.5%    72.9%   100.0%   152.9%   440.4%   483.3%   622.0%   655.7%
[16] (Mplx) /api/zzz26/789       35.6661     2.2%     2.2%     2.7%     3.4%    14.4%    14.5%    16.2%    16.7%    17.1%    17.7%    17.8%    26.1%    28.5%    47.7%    65.4%   100.0%   288.0%   316.0%   406.7%   428.7%
[17] (Sina) /api/aaa01          102.7069     0.8%     0.8%     0.9%     1.2%     5.0%     5.0%     5.6%     5.8%     5.9%     6.1%     6.2%     9.0%     9.9%    16.6%    22.7%    34.7%   100.0%   109.7%   141.2%   148.9%
[18] (Sina) /api/aaa01/123      112.6892     0.7%     0.7%     0.9%     1.1%     4.6%     4.6%     5.1%     5.3%     5.4%     5.6%     5.6%     8.2%     9.0%    15.1%    20.7%    31.6%    91.1%   100.0%   128.7%   135.7%
[19] (Sina) /api/zzz26          145.0454     0.5%     0.5%     0.7%     0.8%     3.5%     3.6%     4.0%     4.1%     4.2%     4.4%     4.4%     6.4%     7.0%    11.7%    16.1%    24.6%    70.8%    77.7%   100.0%   105.4%
[20] (Sina) /api/zzz26/789      152.9070     0.5%     0.5%     0.6%     0.8%     3.4%     3.4%     3.8%     3.9%     4.0%     4.1%     4.1%     6.1%     6.6%    11.1%    15.3%    23.3%    67.2%    73.7%    94.9%   100.0%
