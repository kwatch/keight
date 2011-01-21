###
### $Release: $
### $Copyright: copyright(c) 2011 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


module K8


  class MultiPart

    def initialize(boundary=nil)
      @boundary = boundary || new_boundary()
      @values = []
    end

    attr_reader :boundary

    def add_str(name, value)
    end

    def new_boundary
      seed = [rand(), rand(), rand(), Time.now.to_f].pack('ffff')
      Digest::SHA1.hexdigest(seed)
    end

  end



end
