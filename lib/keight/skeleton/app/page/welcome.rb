# -*- coding: utf-8 -*-

require 'keight'

require_relative '../action'


class WelcomePage < My::Action

  mapping ''        , :GET=>:do_index

  def do_index
    #"<h1>Welcome!</h1>"
    render_html :welcome
  end

end
