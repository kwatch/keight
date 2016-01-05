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
    #{"message"=>"Hello"}   # JSON
    "<h1>Hello</h1>"        # HTML
  end

  def do_show(id)
    ## 'id' or 'xxx_id' will be converted into integer.
    "<h1>Hello: id=#{id.inspect}</h1>"
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
require './hello'

mapping = [
  ['/api', [
    ['/hello'     , HelloAction],
    ## or
    #['/hello'    , "./hello:HelloAction"],
  ]],
]
app = K8::RackApplication.new(mapping)

run app
```

Open http://localhost:8000/api/hello or http://localhost:8000/api/hello/123
with your browser.

Do you like it? If so, try `k8rb project myapp1` to generate project skeleton.

```console
$ mkdir gems                         # if necessary
$ export GEM_HOME=$PWD/gems          # if necessary
$ export PATH=$GEM_HOME/bin:$PATH    # if necessary
$ gem install -N keight
$ k8rb help                          # show help
$ k8rb project myapp1                # create new project
$ cd myapp1/
$ rake setup                         # install gems and download libs
$ export APP_ENV=dev    # 'dev', 'prod', or 'stg'
$ k8rb help mapping
$ k8rb mapping                       # list urlpath mappings
$ k8rb mapping --format=javascript   # or jquery,angular,json,yaml
$ k8rb configs                       # list config parameters
$ rake server port=8000
$ open http://localhost:8000/
$ ab -n 10000 -c 100 http://localhost:8000/api/hello
```


CheatSheet
----------

```ruby
require 'keight'

class HelloAction < K8::Action

  ## mapping
  mapping '',              :GET=>:do_hello_world
  mapping '/{name:\w+}',   :GET=>:do_hello

  ## request, response, and helpers

  def do_hello_world
    do_hello('World')
  end

  def do_hello(name)

    ## request
    @req                   # K8::Request object (!= Rack::Request)
    @req.env               # Rack environment
    @req.method            # ex: :GET, :POST, :PUT, ...
    @req.request_method    # ex: "GET", "POST", "PUT", ...
    @req.path              # ex: '/api/hello'
    @req.query             # query string (Hash)
    @req.form              # form data (Hash)
    @req.multipart         # multipart form data ([Hash, Hash])
    @req.json              # JSON data (Hash)
    @req.params            # query, form, multipart or json
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
      return [JSON.dump(content)]
    end
    super
  end

  def handle_exception(ex)   # exception handler
    meth = "on_#{ex.class.name}"
    return __send__(meth, ex) if respond_to?(meth)
    super
  end

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
                     , './app/api/book_comments:BookCommentsAPI'],
    ['/orders'       , './app/api/orders:OrdersAPI'],
  ]],
]

## application
opts = {
  urlpath_cache_size:  0,    # 0 means cache disabled
}
app = K8::RackApplication.new(urlpath_mapping, opts)

## misc
p HelloAction[:do_update].method        #=> :GET
p HelloAction[:do_update].urlpath(123)  #=> "/api/books/123"
p HelloAction[:do_update].form_action_attr(123)
                                        #=> "/api/books/123?_method=PUT"
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

URL path parameter `{id}` and `{xxx_id}` are regarded as `{id:\d+}` and
`{xxx_id:\d+}` respectively and converted into positive interger automatically.
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
`{date:\d\d\d\d-\d\d-\d\d}` and `{xxx_date:\d\d\d\d-\d\d-\d\d}` respectively
and converted into Date object automatically.
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

**If you specify `{id:\d+}` or `{date:\d\d\d\d-\d\d-\d\d}` explicitly,
URL path parameter value is not converted into integer nor Date object.**
In other words, you can cancel automatic conversion by specifing regular
expression of URL path parameters.


### Nested Routing

```ruby
urlpath_mapping = [
    ['/api', [
        ['/books'                      , BookAPI],
        ['/books/{book_id}/comments'   , BookCommentsAPI],
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
$ k8rb project myapp1
$ cd myapp1/
$ k8rb mapping --format=javascript | less  # or 'jquery', 'angular'
$ mkdir -p static/js
$ jsfile=static/js/urlpath_mapping.js
$ rm -f $jsfile
$ echo 'var Mapping = {'           >> $jsfile
$ k8rb mapping --format=javascript >> $jsfile
$ echo '};'                        >> $jsfile
```


### Download JavaScript Libraries

Keight.rb can download Javascript or CSS libraries from [cdnjs.com].
It is good idea to make layout of JavaScript libraries to be same as CDN.

[cdnjs.com]: https://cdnjs.com/

```console
$ k8rb project myapp1
$ cd myapp1/
$ k8rb help cdnjs
$ k8rb cdnjs                 # list libraries
$ k8rb cdnjs 'jquery*'       # search libraries
$ k8rb cdnjs jquery          # list versions
$ k8rb cdnjs jquery 2.1.4    # download library
## or
$ k8rb cdnjs --basedir=static/lib jquery 2.1.4
```


FAQ
---

#### Why Keight.rb is so fast?

I don't think Keight.rb is so fast. Other frameworks are just too slow.

**You should know that Rails is slow due to Rails itself, and not to Ruby.**


#### How to setup template engine?

Try `k8rb project myapp1; cd myapp1; less app/action.rb`.


#### How to support static files?

Try `k8rb project myapp1; cd myapp1; less app/action.rb`.


#### How to setup session?

Try `k8rb project myapp1; cd myapp1; less config.ru`.


#### Can I use Rack::Request and Rack::Response instead of Keight's?

Try `K8::REQUEST_CLASS = Rack::Request; K8::RESPONSE_CLASS = Rack::Response`.


License and Copyright
---------------------

$License: MIT License $

$Copyright: copyright(c) 2014-2016 kuwata-lab.com all rights reserved $
