###
### $Release: $
### $Copyright: copyright(c) 2010-2011 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


module K8


  class Assertion < StandardError
  end


  module_function


  def assertion_failed(message)
    ex = Assertion.new(message)
    ex.set_backtrace(caller())
    raise ex
  end


end
