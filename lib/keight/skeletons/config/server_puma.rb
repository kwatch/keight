# -*- coding: utf-8 -*-

## usage: puma -C config/server_puma.rb
## ref: https://github.com/puma/puma

environment 'production'
port 9292
daemonize false
threads 8,32
workers 3
preload_app!

on_worker_boot do
  ##
  ## configuration here
  ##

  #ActiveSupport.on_load(:active_record) do
  #  ActiveRecord::Base.establish_connection
  #end

end
