# -*- coding: utf-8 -*-

#require "bundler/gem_tasks"

#require 'rake/testtask'
#Rake::TestTask.new(:test) do |t|
#  t.libs << "test"
#  t.test_files = FileList['test/**/*_test.rb']
#  #t.verbose = true
#end

desc "run test scripts"
task :test do
  files = [
    './test/**/*_test.rb',
  ]
  code = 'ARGV.each {|p| Dir.glob(p).each {|f| require f } }'
  system "ruby -v"
  system "ruby", "-e", code, *files
end

task :default => :test


def run(command)
  print "[rake]$ "
  sh command
end

def gem_home_required
  return if ENV['GEM_HOME']
  $stderr.puts <<'END'
***
*** ERROR: $GEM_HOME environment variable required.
***
*** (MacOSX, Linux)
***   $ mkdir gems
***   $ export GEM_HOME=$PWD/gems
***
*** (Windows)
***   $ md gems
***   $ set GEM_HOME=%CD%\gems
***
END
  exit 1
end


desc "start server process"
task :server do |t|
  port = ENV['port'] || ENV['PORT'] || 8000
  run "rackup -p #{port} -E production -s puma config.ru"
end


desc "install gems and download libs"
task :setup => ['setup:gems', 'setup:static']

namespace :setup do

  desc "install required libraries"
  task :gems do |t|
    gem_home_required()
    run "gem install bundler"
    puts ""
    run "bundler install"
  end

  desc "download jquery.js etc from cdnjs"
  task :static do |t|
    filename = "app/template/_layout.html.eruby"
    rexp = %r'<script src=".*?\/([-.\w]+)\/(\d+(?:\.\d+)+[-.\w]+)/[^"]*?\.js"'
    done = {}
    File.read(filename).scan(rexp) do
      library, version = $1, $2
      key = "#{library}--#{version}"
      unless done[key]
        run "k8rb cdnjs #{library} #{version}"
        done[key] = true
      end
    end
  end

end
