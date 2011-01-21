###
### $Release: $
### $Copyright: copyright(c) 2011 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

$: << "#{File.dirname(__FILE__)}"
$: << "#{File.dirname(File.dirname(__FILE__))}/lib"

require 'oktest'

require 'small_eruby'


class SmallEruby::Context_TC
  include Oktest::TestCase

  def test_initialize
    spec "takes Hash object and populates as instance variables." do
      hash = {:x=>10, :y=>nil}
      c = SmallEruby::Context.new(hash)
      ok {c.instance_variable_get('@x')} == 10
      ok {c.instance_variable_get('@y')} == nil
      ok {c.instance_variables.collect {|x| x.to_s }.sort} == ['@x', '@y']
    end
  end

  def test_h
    spec "escaps html special chars." do
      hash = {:x=>10, :y=>nil}
      c = SmallEruby::Context.new(hash)
      ok {c.__send__(:h, '& < > "')} == '&amp; &lt; &gt; &quot;'
    end
  end

end


class SmallEruby_TC
  include Oktest::TestCase

  def test_convert
    spec "converts eRuby code into ruby script." do
      input = <<'END'
<table>
<% for item in @items %>
  <tr>
    <td></td>
  </tr>
<% end %>
</table>
END
    end

  end

end


if __FILE__ == $0
  Oktest.run_all()
end

