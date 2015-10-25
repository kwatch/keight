# -*- coding: utf-8 -*-

class Config

  add :app_env      , ENV['APP_ENV']  , "environment name"

  ## database
  add :db_host      , 'localhost'     , "DB host name"
  add :db_port      , 5432            , "DB port number"
  add :db_name      , 'xxxx'          , "DB database"
  add :db_user      , 'xxxx'          , "DB user name"
  add :db_pass      , SECRET          , "DB password"

  ## Rack::Session::Cookie
  add :session_key           , 'rack.session'   , "cookie name"
  add :session_domain        , nil              , "cookie domain"
  add :session_path          , '/'              , "cookie path"
  add :session_expire_after  , 24 * 60 * 60     , "cookie expires"
  add :session_secret        , SECRET           , "secret key"
  add :session_old_secret    , SECRET           , "old secret key"

  ## K8::RackApplication
  add :k8_rackapp_urlpath_cache_size , 0        , "0: cache disabled"

  ## add your own configs here
  add :google_analytics_code , nil              , "ex: 'UA-XXXXX-X'"

end
