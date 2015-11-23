# -*- coding: utf-8 -*-

require_relative '../test_helper'


http  = Rack::TestApp.wrap($main_app)


describe HelloAPI do


  describe 'GET /api/hello' do

    it "returns JSON data." do
      r = http.GET('/api/hello')
      result = http.GET('/api/hello')
      r = result
      ok {r.status} == 200
      ok {r.content_type} == "application/json"
      #ok {r.body_json} == {"message"=>"Hello"}
      ok {r.body_json} == {"action"=>"index", "query"=>{}}
    end

  end


end
