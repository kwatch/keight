# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

desc "do test"
task :test do |t|
  for fname in Dir.glob('test/test_*.rb')
    sh "ruby #{fname}"
  end
end
