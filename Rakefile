# -*- coding: utf-8 -*-

###

RELEASE   = ENV['rel'] || '0.0.0'
COPYRIGHT = 'copyright(c) 2014-2016 kuwata-lab.com all rights reserved'
LICENSE   = 'MIT License'

PROJECT   = 'keight'

###

task :default => :test

def edit_content(content)
  s = content
  s = s.gsub /\$Release\:.*?\$/,   "$Release\: #{RELEASE} $"
  s = s.gsub /\$Copyright\:.*?\$/, "$Copyright\: #{COPYRIGHT} $"
  s = s.gsub /\$License\:.*?\$/,   "$License\: #{LICENSE} $"
  s = s.gsub /\$Release\$/,   RELEASE
  s = s.gsub /\$Copyright\$/, COPYRIGHT
  s = s.gsub /\$License\$/,   LICENSE
  s
end


desc "run test scripts"
task :test do
  #sh "ruby -r minitest/autorun test/*_test.rb"
  sh "ruby test/#{PROJECT}_test.rb"
end


desc "remove *.rbc"
task :clean do
  rm_f [Dir.glob("lib/**/*.rbc"), Dir.glob("test/**/*.rbc")]
end


desc "copy files into 'dist/#{RELEASE}'"
task :dist => :clean do
  require_release_number()
  spec_src = File.open("#{PROJECT}.gemspec") {|f| f.read }
  spec = eval spec_src
  dir = "dist/#{RELEASE}"
  rm_rf dir
  mkdir_p dir
  sh "tar cf - #{spec.files.join(' ')} | (cd #{dir}; tar xvf -)"
  spec.files.each do |fpath|
    next if fpath =~ /\.(gz|jpg|png|form)\z/
    #filepath = File.join(dir, fpath)
    #content = File.open(filepath, 'rb:utf-8') {|f| f.read }
    #new_content = edit_content(content)
    #File.open(filepath, 'wb:utf-8') {|f| f.write(new_content) }
    content = File.open(File.join(dir, fpath), 'r+b:utf-8') do |f|
      content = f.read
      new_content = edit_content(content)
      f.rewind()
      f.truncate(0)
      f.write(new_content)
    end
  end
end


desc "create rubygem pacakge"
task :package => :dist do
  require_release_number()
  chdir "dist/#{RELEASE}" do
    sh "gem build *.gemspec"
  end
  mv Dir.glob("dist/#{RELEASE}/*.gem"), 'dist'
end


desc "release gem"
task :release => :package do
  require_release_number()
  sh "git tag ruby-#{RELEASE}"
  chdir "dist" do
    sh "gem push #{PROJECT}-#{RELEASE}.gem"
  end
end


def require_release_number
  if RELEASE == '0.0.0'
    $stderr.puts "*** Release number is not speicified"
    $stderr.puts "*** Usage: rake <task> rel=X.X.X"
    raise StandardError
  end
end
