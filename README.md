Keight.rb README
================

($Release: 0.0.0 $)


Overview
--------

Keight.rb is the very fast web application framework for Ruby.
It is about 100 times faster than Rails and 20 times faster than Sinatra.

*Keight.rb is under development and is subject to change without notice.*


Benchmarks
----------

Measured with `app.call(env)` style in order to exclude server overhead:

| Framework | Request            | usec/req | req/sec  |
|:----------|:-------------------|---------:|---------:|
| Rails     | GET /api/hello     |    738.7 |   1353.7 |
| Rails     | GET /api/hello/123 |    782.2 |   1278.4 |
| Sinatra   | GET /api/hello     |    144.1 |   6938.3 |
| Sinatra   | GET /api/hello/123 |    158.4 |   6313.8 |
| Rack      | GET /api/hello     |      9.9 | 101050.9 |
| Keight    | GET /api/hello     |      7.6 | 132432.8 |
| Keight    | GET /api/hello/123 |     10.6 |  94705.9 |

* Ruby     2.2.3
* Rails    4.2.4
* Sinatra  1.4.6
* Rack     1.6.4 (= Rack::Request + Rack::Response)
* Keight   0.1.0

(Script: https://gist.github.com/kwatch/c634e91d2d6a6c4b1d40 )


Quick Tutorial
--------------

```console
$ ruby -v     # required Ruby >= 2.0
ruby 2.2.3p173 (2015-08-18 revision 51636) [x86_64-darwin14]
$ mkdir gems
$ export GEM_HOME=$PWD/gems
$ export PATH=$GEM_HOME/bin:$PATH

$ gem install keight
$ vi hello.rb      # see below
$ vi config.ru     # != 'config.rb'
$ rackup -p 8000 config.ru
```

hello.rb:

```ruby
# -*- coding: utf-8 -*-
require 'keight'

class HelloAction < K8::Action

  mapping ''       , :GET=>:do_index, :POST=>:do_create
  mapping '/{id}'  , :GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete

  def do_index
    return {"message"=>"Hello"}   # JSON
    #return "<h1>Hello</h1>"      # HTML
  end

  def do_show(id)
    ## 'id' or 'xxx_id' will be converted into integer.
    return {"id"=>id}
    #return "<h1>id=#{id.inspect}</h1>"
  end

  def do_create    ; "<p>create</p>"; end
  def do_update(id); "<p>update</p>"; end
  def do_delete(id); "<p>delete</p>"; end

end
```

config.ru:

```ruby
# -*- coding: utf-8 -*-
require 'keight'

mapping = [
  ['/api', [
    ['/hello'    , "./hello:HelloAction"],
    ### or
    #['/hello'     , HelloAction],
  ]],
]
app = K8::RackApplication.new(mapping)

run app
```

Open http://localhost:8000/api/hello or http://localhost:8000/api/hello/123
with your browser.

Do you like it? Try the following steps to generate your project.

```console
$ mkdir gems                         # if necessary
$ export GEM_HOME=$PWD/gems          # if necessary
$ export PATH=$GEM_HOME/bin:$PATH    # if necessary

$ gem install boilerpl8
$ boilerpl8 github:kwatch/keight-ruby myapp1
## select CSS framework
**    1. None
**    2. Bootstrap
**    3. Pure (recommended)
** Which CSS framework do you like? [1-3]: 1

$ cd myapp1
$ export APP_MODE=dev                # 'dev', 'prod', or 'stg'
$ rake -T
$ ls public
$ rake server port=8000
$ open http://localhost:8000/
$ ab -n 10000 -c 100 http://localhost:8000/api/hello.json
```


Command `k8rb`
--------------

Keight.rb provices `k8rb`.

* `k8rb project myapp1` creates new project.  
  This is equvarent to `boilerpl8 github:kwatch/keight-ruby myapp1`.

* `k8rb cdnjs -d static/lib jquery 3.1.0` downloads jQuery files
  from cdnjs.com and stores into `static/lib` directory.  
  This is equivarent to `cdnget cdnjs jquery 3.1.0 static/lib`.

`k8rb` command is provided mainly for backward compatibility.
You can use [boilerpl8](https://github.com/kwatch/boilerpl8/tree/ruby)
and [cdnget](https://github.com/kwatch/cdnget/tree/ruby-release)
inead of `k8rb project` and `k8rb cdnjs`.
`k8rb` is specific to Keight.rb, but both boilerpl8 and cdnget are
available in any project.


CheatSheet
----------

```ruby
require 'keight'

class HelloAction < K8::Action

  ## mapping
  mapping ''             , :GET=>:do_hello_world
  mapping '/{name:str}'  , :GET=>:do_hello

  ## request, response, and helpers

  def do_hello_world
    do_hello('World')
  end

  def do_hello(name)

    ## request
    @req                   # K8::Request object (!= Rack::Request)
    @req.env               # Rack environment
    @req.meth              # ex: :GET, :POST, :PUT, ...
    @req.request_method    # ex: "GET", "POST", "PUT", ...
    @req.path              # ex: '/api/hello'
    @req.query             # query string (Hash)
    @req.form              # form data (Hash)
    @req.multipart         # multipart form data ([Hash, Hash])
    @req.json              # JSON data (Hash)
    @req.params            # query, form or json (except multipart!)
    @req.cookies           # cookies (Hash)
    @req.xhr?              # true when requested by jQuery etc
    @req.client_ip_addr    # ex: '127.0.0.1'

    ## response
    @resp                  # K8::Response object (!= Rack::Response)
    @resp.status_code      # ex: 200
    @resp.status           # alias of @resp.status_code
    @resp.headers          # Hash object
    @resp.set_cookie(k, v) # cookie
    @resp.content_type     # same as @resp.headers['Content-Type']
    @resp.content_length   # same as @resp.headers['Content-Length'].to_i

    ## session (requires Rack::Session)
    @sess[key] = val       # set session data
    @sess[key]             # get session data

    ## helpers
    token = csrf_token()   # get csrf token
    validation_failed()    # same as @resp.status_code = 422
    return redirect_to(location, 302, flash: "message")
    return send_file(filepath)

  end


  ## hook methods

  def before_action        # setup
    super
  end

  def after_action(ex)     # teardown
    super
  end

  def handle_content(content)   # convert content
    if content.is_a?(Hash)
      @resp.content_type = 'application/json'
      return JSON.dump(content)
    end
    super
  end

  def handle_exception(ex)   # exception handler
    proc_ = WHEN_RAISED[ex.class]
    return self.instance_exec(ex, &proc_) if proc_
    super
  end

  WHEN_RAISED = {}
  WHEN_RAISED[NotFound]     = proc {|ex| ... }
  WHEN_RAISED[NotPermitted] = proc {|ex| ... }

  def csrf_protection_required?
    x = @req.method
    return x == :POST || x == :PUT || x == :DELETE
  end

end

## urlpath mapping
urlpath_mapping = [
  ['/'               , './app/page/welcome:WelcomePage'],
  ['/api', [
    ['/books'        , './app/api/books:BooksAPI'],
    ['/books/{book_id}/comments'
                     , './app/api/books:BookCommentsAPI'],
    ['/orders'       , './app/api/orders:OrdersAPI'],
  ]],
]

## application
opts = {
  urlpath_cache_size:  0,    # 0 means cache disabled
}
app = K8::RackApplication.new(urlpath_mapping, opts)

## misc
p HelloAction[:do_update].meth          #=> :GET
p HelloAction[:do_update].path(123)     #=> "/api/books/123"
p HelloAction[:do_update].form_action_attr(123)
                                        #=> "/api/books/123?_method=PUT"
```


URL Mapping
-----------

Rails-like mapping:

```ruby
class BookAPI < K8::Action

  mapping ''       , :GET=>:do_index, :POST=>:do_create
  mapping '/new'   , :GET=>:do_new
  mapping '/{id}'  , :GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete
  mapping '/{id}/edit', :GET=>:do_edit

  def do_index()   ; {list: []}; end
  def do_create()  ; {list: []}; end
  def do_new()     ; {item: id}; end
  def do_show(id)  ; {item: id}; end
  def do_edit(id)  ; {item: id}; end
  def do_update(id); {item: id}; end
  def do_delete(id); {item: id}; end

end
```

Data type and pattern:

```ruby
class BookAPI < K8::Action

  ##
  ## data type and pattern
  ##
  mapping '/{name:str<[^/]+>}' , :GET=>:do_show1
  mapping '/{id:int<\d+>}'     , :GET=>:do_show2
  mapping '/{birthday:date<\d\d\d\d-\d\d-\d\d>}', :GET=>:do_show3

  ##
  ## default pattern
  ##  - '/{name:str}' is same as '/{name:str<[^/]+>}'
  ##  - '/{id:int}' is same as '/{id:int<\d+>}'
  ##  - '/{birthday:date}' is same as '/{birthday:date<\d\d\d\d-\d\d-\d\d>}'
  ##
  mapping '/{name:str}'        , :GET=>:do_show1
  mapping '/{id:int}'          , :GET=>:do_show2
  mapping '/{birthday:date}'   , :GET=>:do_show3

  ##
  ## default data type
  ##  - 'id' and '*_id' are int type
  ##  - 'date' and '*_date' are date type
  ##  - others are str type
  ##
  mapping '/{name}'      , :GET=>:do_show1   # same as '{name:str}'
  mapping '/{id}'        , :GET=>:do_show2   # same as '{id:int}'
  mapping '/{birth_date}', :GET=>:do_show3   # same as '{birth_date:date}'

  ##
  ## pattern with default data type
  ##
  mapping '/{code:<[A-Z]{3}>}', ...  # same as '/{code:str<[A-Z]{3}>'
  mapping '/{id:<[1-9]\d*>}'  , ...  # same as '/{id:int<\d{4}>}'

end
```

URL mapping helper:

```ruby
## for example
p BookAPI[:do_index].meth        #=> :GET
p BookAPI[:do_index].path        #=> "/api/books"
p BookAPI[:do_create].meth       #=> :POST
p BookAPI[:do_create].path       #=> "/api/books"
p BookAPI[:do_show].meth         #=> :GET
p BookAPI[:do_show].path(123)    #=> "/api/books/123"
p BookAPI[:do_update].meth       #=> :PUT
p BookAPI[:do_update].path(123)  #=> "/api/books/123"
p BookAPI[:do_delete].meth       #=> :DELETE
p BookAPI[:do_delete].path(123)  #=> "/api/books/123"
```

Show URL mappings:

```console
$ boilerpl8 github:kwatch/keight-ruby myapp1
$ cd myapp1
$ rake mapping:text       # list url mapping
$ rake mapping:yaml       # list in YAML format
$ rake mapping:json       # list in JSON format
$ rake mapping:jquery     # list for jQuery
$ rake mapping:angularjs  # list for AngularJS
```


Topics
------


### Make Routing More Faster

Specify `urlpath_cache_size: n` (where n is 100 or so) to
`K8::RackApplication.new()`.

```ruby
urlpath_mapping = [
  ....
]
rack_app = K8::RackApplication.new(urlpath_mapping,
                                   urlpath_cache_size: 100)  # !!!
```

In general, there are two type of URL path pattern: fixed and variable.

* Fixed URL path pattern doesn't contain any URL path parameter.<br>
  Example: `/`, `/api/books`, `/api/books/new`.
* Variable URL path pattern contains one or more URL path parameters.<br>
  Example: `/api/books/{id}`, `/api/books/new.{format:html|json}`.

Keight.rb caches fixed patterns and doesn't variable ones, therefore
routing for fixed URL path is faster than variable one.

If `urlpath_cache_size: n` is specified, Keight.rb caches latest `n` entries
of request path matched to variable URL path pattern.
This will make routing for variable one much faster.


### Default Pattern of URL Path Parameter

URL path parameter `{id}` and `{xxx_id}` are regarded as `{id:int<\d+>}` and
`{xxx_id:int<\d+>}` respectively and converted into positive interger automatically.
For example:

```ruby
class BooksAction < K8::Action
  mapping '/{id}', :GET=>:do_show
  def do_show(id)
    p id.class    #=> Fixnum
    ....
  end
end
```

URL path parameter `{date}` and `{xxx_date}` are regarded as
`{date:date<\d\d\d\d-\d\d-\d\d>}` and `{xxx_date:date<\d\d\d\d-\d\d-\d\d>}`
respectively and converted into Date object automatically.
For example:

```ruby
class BlogAPI < K8::Action
  mapping '/{date}', :GET=>:list_entries
  def list_entries(date)
    p date.class    #=> Date
    ....
  end
end
```

If you don't like auto-convert, specify data type and pettern explicitly.
For example, `{id:str<\d+>}` or `{date:str<\d\d\d\d-\d\d-\d\d>}`.


### Nested Routing

```ruby
urlpath_mapping = [
    ['/api', [
        ['/books'                    , "./app/api/books:BookAPI"],
        ['/books/{book_id}/comments' , "./app/api/books:BookCommentsAPI"],
    ]],
]
```


### URL Path Helpers

```ruby
p BooksAPI[:do_index].method          #=> :GET
p BooksAPI[:do_index].urlpath()       #=> "/api/books"

p BooksAPI[:do_update].method         #=> :PUT
p BooksAPI[:do_update].urlpath(123)   #=> "/api/books/123"
p BooksAPI[:do_update].form_action_attr(123)   #=> "/api/books/123?_method=PUT"
```

(Notice that these are availabe after `K8::RackApplication` object is created.)


### Routing for JavaScript

Keight.rb can generate JavaScript routing file.

```console
$ boilerpl8 github:kwatch/keight-ruby myapp1
$ cd myapp1
$ rake mapping:text         # list URL path mapping
$ rake mapping:yaml         # list in YAML format
$ rake mapping:json         # list in JSON format
$ rake mapping:jquery       # list for jQuery
$ rake mapping:angularjs    # list for AngularJS
```


### Download JavaScript Libraries

Install `cdnget` gem in order to download such as jQuery or Bootstrap.

```console
$ gem install cdnget
$ cdnget                                 # list CDN
$ cdnget cdnjs                           # list libraries
$ cdnget cdnjs 'jquery*'                 # search libraries
$ cdnget cdnjs jquery                    # list versions
$ cdnget cdnjs jquery 2.2.4              # list files
$ cdnget cdnjs jquery 2.2.4 static/lib   # download files
static/lib/jquery/2.2.4/jquery.js ... Done (257,551 byte)
static/lib/jquery/2.2.4/jquery.min.js ... Done (85,578 byte)
static/lib/jquery/2.2.4/jquery.min.map ... Done (129,572 byte)

$ ls static/lib/jquery/2.2.4
jquery.js	jquery.min.js	jquery.min.map
```


FAQ
---

#### Why Keight.rb is so fast?

I don't think Keight.rb is so fast. Other frameworks are just too slow.

**You should know that Rails is slow due to Rails itself, and not to Ruby.**


#### How to setup template engine?

Try `k8rb project myapp1; less myapp1/app/action.rb`.
(or `boilerpl8 github:kwatch/keight-ruby myapp1; less myapp1/app/action.rb`).


#### How to support static files?

Try `k8rb project myapp1; less myapp1/app/action.rb`.
(or `boilerpl8 github:kwatch/keight-ruby myapp1; less myapp1/app/action.rb`).


#### How to setup session?

Try `k8rb project myapp1; less myapp1/app/config.ru`.
(or `boilerpl8 github:kwatch/keight-ruby myapp1; less myapp1/app/config.ru`).


#### Can I use Rack::Request and Rack::Response instead of Keight's?

Try `K8::RackApplication::REQUEST_CLASS = Rack::Request` and
`K8::RackApplication::RESPONSE_CLASS = Rack::Response`.


License and Copyright
---------------------

$License: MIT License $

$Copyright: copyright(c) 2014-2016 kuwata-lab.com all rights reserved $
