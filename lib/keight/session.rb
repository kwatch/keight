###
### $Release: $
### $Copyright: copyright(c) 2011 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

module K8


  class Session

    PRIVATE_KEY = 'bd40365a5a3e6820595bae8e7c21f73843db86dbc1b4cc6b4b33d85877ca4741'

    def self.PRIVATE_KEY=(val)
      remove_const :PRIVATE_KEY
      const_set :PRIVATE_KEY, val
    end

    attr_accessor :id

    def new_id()
      @id = Digest::SHA256.hexdigest(new_seed() + PRIVATE_KEY)
      return @id
    end

    private

    def new_seed()
      # I belive that Ruby's rand() generates enough random number!
      return [rand(), rand(), rand(), rand(), Time.now.to_f, $$].pack('ddddds')
    end

  end


  class CookieStoreSession < Session
  end


  class FileStoreSession < Session
  end


end
