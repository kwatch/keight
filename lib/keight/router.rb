# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


module K8


  class Router

    def initialize
      @rexp_mappings = []    # [ [req_path, regexp, {req_method=>action_method}] ]
      @fixed_mappings = {}   # { req_path => {req_method=>action_method} }
    end

    def map(path_pattern, hash)
      #: if hash key is String then converts it into Symbol.
      hash.keys.each do |k|
        hash[k.intern] = hash.delete(k) if k.is_a?(String)
      end
      #: if path_pattern doesn't start with '/' then raise error, except empty path.
      path_pattern.empty? || path_pattern[0] == ?/  or
        raise "#{path_pattern.inspect}: expected to start with '/'."
      #: if path_pattern contains '<...>'...
      if (rexp = _path_pattern_rexp(path_pattern))
        #: if path pattern is not added yet then add new tuples as regexp mapping.
        arr = @rexp_mappings.find {|a| a[0] == path_pattern }
        if ! arr
          @rexp_mappings << [path_pattern, rexp, hash]
        #: if path_pattern is already added then append req_method and action_method to existing hash object.
        else
          arr[2].update(hash)
        end
      #: if path_pattern doesn't contain '<...>' then add them as fixed mapping.
      else
        (@fixed_mappings[path_pattern] ||= {}).update(hash)
        @fixed_mappings[''] ||= {:GET=>'/'} if path_pattern == '/'
      end
      #: return self.
      return self
    end

    def route(req_path, req_method)    # returns [action_method, args]
      #req_method = req_method.intern unless req_method.is_a?(Symbol)
      #: fixed mapping is prior to rexp mapping.
      #: if matched to fixed mapping...
      if (hash = @fixed_mappings[req_path])
        #: if req_method is not matched then check :ALL.
        #: if neight req_method nor :ALL matched then returns false.
        #: args is always empty if matched to fixed mapping.
        return (hash[req_method] || hash[:ALL] || false), []
      #: if not matched to fixed mapping...
      else
        #: if req_method is not matched then check :ALL.
        #: if neight req_method nor :ALL matched then returns false.
        #: catpured values are returned as args.
        @rexp_mappings.each do |path_pattern, rexp, hash|
          next unless (m = rexp.match(req_path))
          return (hash[req_method] || hash[:ALL] || false), m.captures
        end
        #: return nil if not matched.
        return nil, nil
      end
    end

    COMMON_PATTERNS = {
      'id'   => 'id:(\d+)',
      'name' => 'name:([-\w]+)',
    }

    private

    COMPILED__ = {}        # :nodoc:

    def _path_pattern_rexp(path_pattern)
      #: if path_pattern already exists in cache then return it.
      return COMPILED__[path_pattern] if COMPILED__.key?(path_pattern)
      #: if path_pattern doesn't exist in cache then compile and cache it.
      return COMPILED__[path_pattern] = _compile_path_pattern(path_pattern)
    end

    def _compile_path_pattern(path_pattern)
      pos = 0
      buf = '\A'
      path_pattern.scan(/<(.*?)>/) do
        m = Regexp.last_match
        #: escape strings which is on outside of '<...>'.
        buf << Regexp.escape(path_pattern[pos...m.begin(0)])
        #: '<id>' is regarded as '<id:(\d+)>'.
        #: remove label name ('xxx:') from pattern.
        buf << (COMMON_PATTERNS[$1] || $1).sub(/\A\w+:/, '')
        pos = m.end(0)
      end
      #: if path_pattern doesn't contain '<...>' then return nil.
      return nil if pos == 0
      #: if path_pattern contains '<...>' then return Regexp.
      buf << Regexp.escape(path_pattern[pos..-1]) << '\z'
      return Regexp.compile(buf)
    end

  end


end
