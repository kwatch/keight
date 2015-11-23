# -*- coding: utf-8 -*-


Gem::Specification.new do |o|
  o.name          = "keight"
  o.version       = "$Release: 0.0.0 $".split[1]
  o.author        = "makoto kuwata"
  o.email         = "kwa(at)kuwata-lab.com"
  o.platform      = Gem::Platform::RUBY
  o.homepage      = "https://github.com/kwatch/keight/tree/ruby"
  o.license       = "MIT Lisense"
  o.summary       = "Jet-speed webapp framework for Ruby"
  o.description   = <<'END'
Keight.rb is the crazy-fast webapp framework for Ruby.
It is about 100 times faster than Rails and 20 times faster than Sinatra.

See https://github.com/kwatch/keight/tree/ruby for details.
END

  o.files         = Dir[*%w[
                      README.md MIT-LICENSE keight.gemspec setup.rb Rakefile
                      bin/k8rb
                      lib/keight.rb lib/keight/**/*.{[a-z]*} lib/keight/**/.{[a-z]*}
                      test/*_test.rb test/data/* test/oktest.rb
                      bench/bench.rb bench/benchmarker.rb
                    ]]
                      #lib/keight.rb lib/keight/**/*
  o.executables   = ["k8rb"]
  o.bindir        = ["bin"]
  #o.test_files   = o.files.grep(/^test\//)
  o.test_file     = "test/keight_test.rb"

  o.required_ruby_version = '>= 2.0'
  o.add_runtime_dependency 'rack', '~> 1.6'
  #o.add_development_dependency "oktest", "~> 0"
end
