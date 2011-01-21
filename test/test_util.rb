# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

require "#{File.dirname(__FILE__)}/_setup"


class PrototypeObjectTest
  include Oktest::TestCase

  def test_method_missing
    spec "value which is set by setter is accessible by getter" do
      obj = K8::PrototypeObject.new
      obj.team = "SOS"
      ok_(obj.team) == "SOS"
    end
    spec "getter is propagated to prototype object" do
      obj1 = K8::PrototypeObject.new
      obj2 = K8::PrototypeObject.new(obj1)
      obj1.name = "Haruhi"
      ok_(obj2.name) == "Haruhi"
    end
    spec "getter raises NameError when value not found" do
      obj1 = K8::PrototypeObject.new
      obj2 = K8::PrototypeObject.new(obj1)
      pr = proc { obj2.name }
      ok_(pr).raise?(NameError, /^undefined method `name'/)
    end
    spec "getter with '!' returns nil instead of raising NameError" do
      obj1 = K8::PrototypeObject.new
      obj2 = K8::PrototypeObject.new(obj1)
      begin
        obj2.name!
      rescue => ex
        raise ex
      end
    end
    spec "setter doesn't change prototype" do
      obj1 = K8::PrototypeObject.new
      obj2 = K8::PrototypeObject.new(obj1)
      obj1.name = "Haruhi"
      obj2.name = "Sasaki"
      ok_(obj1.name) == "Haruhi"
      ok_(obj2.name) == "Sasaki"
    end
  end

end
