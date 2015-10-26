# -*- coding: utf-8 -*-

require 'keight'

## create $config object
require_relative 'config'

## get $urlpath_mapping
require_relative 'config/urlpath_mapping'

## create application object
opts = $config.get_all(:k8_rackapp_)   # ex: {urlpath_cache_size: 1000}
app = K8::RackApplication.new($urlpath_mapping, opts)
$urlpath_mapping = nil

## cookie store session
require 'rack/session/cookie'
use Rack::Session::Cookie, $config.get_all(:session_)

## start application
run app
