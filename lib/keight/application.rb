# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


module K8


  class Application

    def initialize(default_controller_class=nil)
      @default_controller_class = default_controller_class
    end

    def call(env)
      req = REQUEST.new(env)
      res = RESPONSE.new
      begin
        content = handle(req, res)
      rescue Exception => ex
        res.status_code = 500
        content = handle_internal_error(req, res, ex)
      end
      return [res.status_code, res.headers, content]
    end

    def handle(req, res)
      klass = @default_controller_class
      if ! klass.urlpath
        ## ex. '/sos/index.cgi' (SCRIPT_PATH) ==> '/sos' (urlpath)
        s = req.env['SCRIPT_NAME']
        klass.urlpath = File.dirname(s) if s && ! s.empty?
      end
      controller = klass.new(req, res)
      ret = controller.handle()
      ret = [ret] if ret.is_a?(String)
      return ret
    end

    def main(env=nil, stdout=$stdout)
      env ||= self.class.set_env_for_cgi(ENV.to_hash())
      status, headers, contents = call(env)
      stdout   << "Status: #{K8::STATUS_CODES[status]}\r\n" unless status == 200
      headers.each do |name, value|
        stdout << "#{name}: #{value}\r\n"
      end
      stdout   << "\r\n"
      contents.each do |str|
        stdout << str
      end
    end

    protected

    def handle_internal_error(req, res, ex)
      context = {:request=>req, :response=>res, :exception=>ex}
      res.content_type = 'text/html'
      template_file = Config[:error_template_file]
      case template_file
      when /\.(tjn|rbhtml)$/
        require 'tenjin'
        output = (@_tmpl ||= Tenjin::Template.new(template_file)).render(context)
      when /\.(eruby|rhtml)$/
        require 'picoerb'
        output = (@_eruby ||= PicoEruby.new.read(template_file)).render(context)
      else
        res.content_type = 'text/plain'
        output = "#{ex.class.name}: #{ex.message}\n"
        max = 30
        ex.backtrace.each_with_index do |s, i|
          output << "    #{s}\n"
          too_long = i >= max
          output << "    ....\n" if too_long
          break                  if too_long
        end
      end
      return [output]
    end

    private

    def self.set_env_for_cgi(env)
      env['rack.version']      = [1, 1]
      env['rack.url_scheme']   = 'http'
      env['rack.input']        = $stdin
      env['rack.error']        = $stderr
      env['rack.multithread']  = false
      env['rack.multiprocess'] = true
      env['rack.run_once']     = true
      env['rack.session']      = nil
      env['rack.logger']       = nil
      return env
    end

  end


end
