# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

require 'annotation'


module K8


  class ActionMetadata

    def initialize(controller_class, request_method, path_pattern, options)
      @controller_class = controller_class
      @request_method   = request_method
      @path_pattern     = path_pattern
      @options          = K8::Util.options2hash(options)
    end

    attr_accessor :request_method, :path_pattern, :options
    attr_accessor :action_method, :action_name
    alias method request_method

    def path(*args)
      @path_format ||= "#{@controller_class.base_path}#{@path_pattern.gsub(/<.*?>/, '%s')}"
      return @path_format % args
    end

    def hidden_tag
      return '' if (req_method = @request_method) == :POST || req_method == :GET
      return "<input type=\"hidden\" name=\"_method\" value=\"#{req_method}\" />"
    end

  end


  class Actions

    def initialize(controller_class)
      @controller_class = controller_class
    end

    def []=(name, metadata)
      instance_variable_set("@#{name}", metadata)
      eval "def self.#{name}; @#{name}; end"
    end

    def [](name)
      return instance_variable_get("@#{name}")
    end

  end


  class BaseController

    def initialize(request=nil, response=nil)
      @_request = request
      @_response = response
    end

    def request;  @_request;  end
    def response; @_response; end
    #def request=(obj);   @_request = obj;   end
    #def response=(obj);  @_response = obj;  end

    def handle
      before()
      return handle_request()
    rescue HttpException => ex
      return handle_http_exception(ex)
    rescue => ex
      return handle_error(ex)
    ensure
      after()
    end

    protected

    def before
    end

    def after
    end

    def handle_request
      raise NotImplementedError.new("#{self.class.name}#handle_request(): not implemented yet.")
    end

    def handle_http_exception(ex)
      @_response.status_code = ex.status_code
      @_response.content_type = 'text/html'
      return <<END
<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>#{STATUS_CODES[ex.status_code]}</title>
</head><body>
<h1>#{STATUS_CODES[ex.status_code]}</h1>
<p>#{K8::Util.h(ex.message)}</p>
</body></html>
END
    end

    def handle_error(ex)
      @_response.status_code = 500
      @_response.content_type = 'text/html'
      return "<h2>#{STATUS_CODES[500]}</h2>"
    end

  end


  module ControllerAnnotations
    extend Annotation

    def GET(method_name, path, *options)
      _new_action_method(method_name, :GET, path, options)
    end

    def POST(method_name, path, *options)
      _new_action_method(method_name, :POST, path, options)
    end

    def PUT(method_name, path, *options)
      _new_action_method(method_name, :PUT, path, options)
    end

    def DELETE(method_name, path, *options)
      _new_action_method(method_name, :DELETE, path, options)
    end

    def HEAD(method_name, path, *options)
      _new_action_method(method_name, :HEAD, path, options)
    end

    def OPTIONS(method_name, path, *options)
      _new_action_method(method_name, :OPTIONS, path, options)
    end

    def TRACE(method_name, path, *options)
      _new_action_method(method_name, :TRACE, path, options)
    end

    def ALL(method_name, path, *options)
      _new_action_method(method_name, :ALL, path, options)
    end

    annotation :GET, :POST, :PUT, :DELETE, :HEAD, :OPTIONS, :TRACE, :ALL

    private

    def _new_action_method(method_name, req_method, path, options)
      md = ActionMetadata.new(self, req_method, path, options)
      #: set action_method and action_name to metadata.
      md.action_method = method_name
      md.action_name   = method_name.to_s.sub(/\Ado_/, '').intern
      #: register metadata into @_actions.
      @_actions[md.action_name] = md
      #: map path_pattern, request_method, and action_method to @_router.
      @_router.map(md.path_pattern, md.request_method => method_name)
    end

  end


  class Controller < BaseController

    def handle_request
      req = @_request
      req_path = req.path
      base_path = self.class.base_path
      if base_path && ! base_path.empty?
        req_path.start_with?(base_path)  or
          raise "assertion: #{req_path.inspect}.start_with?(#{base_path.inspect}): failed."
        req_path = req_path[base_path.length..-1]
      end
      mapped, args = self.class.router.route(req_path, req.method)
      if ! mapped
        mapped.nil? ? http_404_not_found() : http_405_method_not_allowed()
      elsif mapped == '/'
        qs = req.query_string
        location = qs && ! qs.empty? ? "#{req.path}/?#{qs}" : "#{req.path}/"
        redirect_permanently_to(location)
      else
        action_method = mapped
        return __send__(action_method, *args)
      end
    end

    def handle_error(ex)
      super
      arr = ex.backtrace()
      buf = ""
      buf << "<h2>#{STATUS_CODES[500]}</h2>\n"
      buf << "<pre class=\"exception\">"
      buf << "<b>" << K8::Util.h("#{arr[0]}: #{ex.message} (#{ex.class.name})") << "</b>\n"
      block = proc {|s| buf << "        from #{K8::Util.h(s)}\n" }
      max, n = 20, 10
      if arr.length <= max
        arr[1..-1].each(&block)
      else
        arr[1..(max-n)].each(&block)
        buf << "           ...\n"
        arr[-n..-1].each(&block)
      end
      return buf
      buf << "</pre>\n"
      return buf
    end

    def redirect_to(location)
      @_response.add_header('Location', location)
      raise HttpException.new(302, "redirect to #{location}")
    end

    def redirect_permanently_to(location)
      @_response.add_header('Location', location)
      raise HttpException.new(301, "redirect permanently to #{location}")
    end

    def http_403_forbidden(message=nil)
      raise HttpException.new(403, message || "Forbiden.")
    end

    def http_404_not_found(url=nil)
      raise HttpException.new(404, "#{url || @_request.path}: not found.")
    end

    def http_405_method_not_allowed(method=nil)
      raise HttpException.new(405, "#{method || @_request.method}: method not allowed.")
    end

    def validation_failed
      @_response.status_code = 422    # Unprocessable Entity
    end

    def actions
      self.class.actions
    end

    private

    def self.inherited(subclass)
      subclass.class_eval do
        #: subclass will be set Router object.
        @_router  = Router.new
        def self.router;  @_router;  end
        #: subclass will be set Actions object.
        @_actions = Actions.new(subclass)
        def self.actions;  @_actions;  end
        #: subclass will be defined base_path() method.
        @_base_path = nil
        def self.base_path;  @_base_path;  end
        def self.base_path=(path);  @_base_path = path;  end
        def self.mount_to(path);    @_base_path = path;  end
      end
    end

    extend ControllerAnnotations

  end


end
