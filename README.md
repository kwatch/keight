Keight.rb README
================

($Release: 0.0.0 $)


Overview
--------

Keight.rb is the very fast web application framework for Ruby.
It is about 100 times faster than Rails and 20 times faster than Sinatra.


Benchmarks
----------

Measured with `app.call(env)` style in order to exclude server overhead:

| FW      | Request            | sec/1000req | req/sec  |
|:--------|:-------------------|------------:|---------:|
| Rails   | GET /api/hello     |      7.5188 |    133.0 |
| Rails   | GET /api/hello/123 |      8.0030 |    125.0 |
| Sinatra | GET /api/hello     |      1.5034 |    665.2 |
| Sinatra | GET /api/hello/123 |      1.6328 |    612.4 |
| Rack    | GET /api/hello     |      0.0789 |  12674.3 |
| Keight  | GET /api/hello     |      0.0773 |  12936.6 |
| Keight  | GET /api/hello/123 |      0.1385 |   7220.2 |

* Ruby     2.2.3
* Rails    4.2.4
* Sinatra  1.4.6
* Rack     1.6.4 (= Rack::Request + Rack::Response)
* Keight   0.1.0

(Script: https://gist.github.com/kwatch/c634e91d2d6a6c4b1d40 )


Quick Tutorial
--------------

```
$ gem install keight
$ vi hello.rb
$ vi config.ru
$ rackup -c config.ru -p 8000
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

config.rb:

```ruby
# -*- coding: utf-8 -*-
require 'keight'
require './hello'

app = K8::RackApplication.new
app.mount '/hello', HelloAction

run app
```

Open http://localhost:8000/hello or http://localhost:8000/hello/123 by browser.

Do you like it? If so, try `k8rb init myapp1` to generate project skeleton.

```
$ k8rb init myapp1
$ cd myapp1
$ export APP_ENV=dev    # 'dev', 'prod', or 'stg'
$ k8rb mapping
$ k8rb configs
$ rackup -c config.ru -p 8000
$ ab -n 1000000 -c 100 http://127.0.0.1:8000/api/hello
```


CheatSheet
----------

```ruby
require 'keight'

class HelloAction < K8::Action

  ## mapping
  mapping '',    :GET=>:do_hello_world
  mapping '/{name:[a-zA-Z]+}',   :GET=>:do_hello

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
    meth = "on_#{ex.class}"
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
```


FAQ
---

#### Why Keight.rb is so fast?

I don't think Keight.rb is so fast. Other frameworks are just too slow.

**You should know that Rails is slow due to Rails itself, and not to Ruby.**


#### How to setup template engine?

Try `k8rb init myapp1; cd myapp1; less app/action.rb`.


#### How to support static files?

Try `k8rb init myapp1; cd myapp1; less app/action.rb`.


#### How to setup session?

Try `k8rb init myapp1; cd myapp1; less config.ru`.


#### Can I use Rack::Request and Rack::Response instead of Keight's?

Try `K8::REQUEST_CLASS = Rack::Request; K8::RESPONSE_CLASS = Rack::Response`.


#### What `urlpath_cache_size: 0` means?

`K8::RackApplication` can take `urlpath_cache_size: n` keyword arugment.

* If `n == 0` then Keight.rb doesn't cache urlpath mapping containig
  urlpath parameters such as `/api/books/{id}`.
* If `n > 0` then Keight.rb caches latest `n` entries of urlpath mapping
  containing urlpath parameters.
* Keight.rb always caches urlpath mapping which has no urlpath parameters.
  For example, `/api/books` is always cached regardless
  `urlpath_cache_size:` value.

If you need more performance, try `urlpath_cache_size: 1000` or so.


License and Copyright
---------------------

$License: MIT License $

$Copyright: copyright(c) 2014-2015 kuwata-lab.com all rights reserved $
