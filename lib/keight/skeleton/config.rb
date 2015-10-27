# -*- coding: utf-8 -*-

app_env = ENV['APP_ENV']    # 'dev', 'prod', 'stg', 'test'
if app_env.nil? || app_env.empty?
  $stderr.write '
**
** ERROR: Set $APP_ENV environment variable at first.
**
** Example (MacOSX, UNIX):
**    $ export APP_ENV=dev       # development mode
**    $ export APP_ENV=prod      # production mode
**    $ export APP_ENV=stg       # staging mode
**
'
  exit 1
end

if defined?(Config)     # Ruby < 2.2 has obsoleted 'Config' object
  Object.class_eval do
    remove_const :Config
  end
end

## define Config class
require 'keight'
class Config < K8::BaseConfig
end

## load 'app.rb', 'app_xxx.rb' and 'app_xxx.private'
require_relative "config/app"
require_relative "config/app_#{app_env}"
fpath = File.join(File.dirname(__FILE__), "config", "app_#{app_env}.private")
load fpath if File.file?(fpath)

## if SECRET value is left, report error and exit.
errmsg = Config.validate_values()
if errmsg
  $stderr.write(errmsg)
  exit 1
end

## create $config object
$config = Config.new()

## temporary directory to put uploaded files
ENV['K8_UPLOAD_DIR'] = $config.k8_upload_dir if $config.k8_upload_dir
