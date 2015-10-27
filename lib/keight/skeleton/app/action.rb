# -*- coding: utf-8 -*-

require 'keight'
require 'baby_erubis'
require 'baby_erubis/renderer'

require './config'


class StrippedHtmlTemplate < BabyErubis::Html
  def parse(input, *args)
    ## strip spaces of indentation
    stripped = input.gsub(/^[ \t]+</, '<')
    return super(stripped, *args)
  end
end


module My
end


class My::Action < K8::Action


  ##
  ## template
  ##

  include BabyErubis::HtmlEscaper
  include BabyErubis::Renderer

  ERUBY_PATH       = ['app/template']
  ERUBY_LAYOUT     = :_layout
  #ERUBY_HTML      = BabyErubis::Html
  ERUBY_HTML       = StrippedHtmlTemplate
  ERUBY_HTML_EXT   = '.html.eruby'
  ERUBY_TEXT       = BabyErubis::Text
  ERUBY_TEXT_EXT   = '.eruby'
  ERUBY_CACHE      = {}

  protected

  alias render_html eruby_render_html
  alias render_text eruby_render_text


  ##
  ## event handler (= exception handler)
  ##

  protected

  ##
  ## Define event handlers here.
  ##
  ## ex:
  ##   class Event < Exception; end
  ##   class NotExist < Event; end
  ##   class NotPermitted < Event; end
  ##
  ##   def on_NotExist(ev)    # or: define_method "on_Foo::Bar" do |ev|
  ##     @resp.status_code = 404   # 404 Not Found
  ##     {"error"=>"Not exist"}
  ##   end
  ##   def on_NotPermitted(ev)
  ##     @resp.status_code = 403   # 403 Forbidden
  ##     {"error"=>"Not permitted"}
  ##   end
  ##
  ##   def do_show(id)
  ##     item = Item.find(id)  or raise NotExist
  ##     return {"item"=>{"id"=>id, "name"=>item.name}}
  ##   end
  ##


end


class My::AdminAction < My::Action

  ## override template configs
  ERUBY_PATH       = ['admin/template']
  ERUBY_LAYOUT     = :_admin_layout

end


class My::StaticPage  < My::Action

  mapping '/{urlpath:.+}',   :GET=>:do_send_file
  STATIC_DIR = "static"

  def do_send_file(urlpath)
    filepath = "#{STATIC_DIR}/#{urlpath}"
    File.file?(filepath)  or raise K8::HttpException.new(404)
    #env = @req.env
    #header_name = env['sendfile.type'] || env['HTTP_X_SENDFILE_TYPE']
    #if header_name && ! header_name.empty?
    #  @resp.headers[header_name] = filepath
    #  return nil
    #else
      return send_file(filepath)
    #end
  end

end
