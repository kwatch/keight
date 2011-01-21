###
### $Release: $
### $Copyright: copyright(c) 2010-2011 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


require 'tenjin'

require 'keight/controller'
require 'keight/form'
require 'keight/config'

K8::Config[:tenjin_options] = {
  :path    => K8::Config[:template_path],
  :postfix => '.html.tjn',
  :layout  => :_layout,
}


module K8


  Controller.class_eval do
    include Tenjin::ContextHelper
    include Tenjin::HtmlHelper
    include Tenjin::HtmlTagHelper
    include Tenjin::SafeHelper

    def self.tenjin_options
      unless @tenjin_options
        opts = K8::Config[:tenjin_options].dup
        opts[:path] = ["#{self.dirpath}/_templates"] + opts[:path]
        @tenjin_options = opts
      end
      return @tenjin_options
    end

    def self.engine
      @engine ||= Tenjin::Engine.new(self.tenjin_options)
      return @engine
    end

    def render(template_name, layout=true)
      @_rendered = template_name
      return self.class.engine.render(template_name, self, layout)
    end

    def form_helper(*args)
      return FORM_HELPER.new(@_buf, *args)
    end

  end

end
