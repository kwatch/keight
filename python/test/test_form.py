# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

from __future__ import with_statement

import sys, re
import oktest
from oktest import ok, not_ok, spec
import keight as k8

WEEKDAYS = [
    ('mon', 'Monday'),
    ('tue', 'Tuesday'),
    ('wed', 'Wednesday'),
    ('thu', 'Thirsday'),
    ('fri', 'Friday'),
    ('sat', 'Saturday'),
    ('sun', 'Sunday'),
]

class FormHelperTest(object):

    @classmethod
    def before_all(cls):
        cls._bkup = d = {}
        for k in ('escape', 'to_str'):
            if k in globals():
                d[k] = globals()[k]
        globals()['escape'] = k8.escape_html
        globals()['to_str'] = str

    @classmethod
    def after_all(cls):
        for k in cls._bkup:
            globals()[k] = cls._bkup[k]

    def before(self):
        d = {
            'user.name': 'Haruhi',
            'user.passwd': 'SOS',
            'user.upload': '',
            'user.age': '16',
            'user.gender': 'F',
            'user.comment': 'I have no interest in ordinary people!',
            'user.weekday': 'sat',
        }
        self.params = k8.Params(d)
        self.errors = k8.FormErrors()
        self.form_helper = k8.FormHelper(self.params, self.errors)

    def test___init__(self):
        pass

    def test__setup(self):
        pass

    def test_get_value(self):
        pass

    def test__def_input_control(self):
        pass

    def test_text(self):
        k = 'user.name'
        with spec("returns (or prints) text field tag."):
            ret = self.form_helper.text(k, 'Name', 'Required.')
            ok (ret) == r'''
<tr>
 <th>Name</th>
 <td>
  <span><input type="text" name="user.name" value="Haruhi" /></span>
  <div class="desc"><em>(Required.)</em></div>
 </td>
</tr>
'''[1:]
        with spec("if error exists then prints error message."):
            self.params[k] = ''
            self.errors[k] = 'Not entered.'
            ret = self.form_helper.text(k, 'Name', 'Required.')
            ok (ret) == r'''
<tr>
 <th class="has-error">Name</th>
 <td class="has-error">
  <span class="has-error"><input type="text" name="user.name" value="" /></span>
  <div class="error-msg">Not entered.</div>
  <div class="desc"><em>(Required.)</em></div>
 </td>
</tr>
'''[1:]

    def test_password(self):
        k = 'user.passwd'
        with spec("returns (or prints) password field tag."):
            ret = self.form_helper.password(k, 'Password', 'Required.')
            ok (ret) == r'''
<tr>
 <th>Password</th>
 <td>
  <span><input type="password" name="user.passwd" value="SOS" /></span>
  <div class="desc"><em>(Required.)</em></div>
 </td>
</tr>
'''[1:]
        with spec("if error exists then prints error message."):
            self.params[k] = 'xxxxxxxxxxxxxxxxxxxx'
            self.errors[k] = 'Too long.'
            ret = self.form_helper.password(k, 'Password', 'Required.')
            ok (ret) == r'''
<tr>
 <th class="has-error">Password</th>
 <td class="has-error">
  <span class="has-error"><input type="password" name="user.passwd" value="xxxxxxxxxxxxxxxxxxxx" /></span>
  <div class="error-msg">Too long.</div>
  <div class="desc"><em>(Required.)</em></div>
 </td>
</tr>
'''[1:]

    def test_file(self):
        k = 'user.upload'
        with spec("returns (or prints) file field tag."):
            ret = self.form_helper.file(k, 'Upload', 'Upload image file.')
            ok (ret) == r'''
<tr>
 <th>Upload</th>
 <td>
  <span><input type="file" name="user.upload" /></span>
  <div class="desc"><em>(Upload image file.)</em></div>
 </td>
</tr>
'''[1:]
        with spec("if error exists then prints error message."):
            self.params[k] = ''
            self.errors[k] = 'Invalid file type.'
            ret = self.form_helper.file(k, 'Upload', 'Upload image file.')
            ok (ret) == r'''
<tr>
 <th class="has-error">Upload</th>
 <td class="has-error">
  <span class="has-error"><input type="file" name="user.upload" /></span>
  <div class="error-msg">Invalid file type.</div>
  <div class="desc"><em>(Upload image file.)</em></div>
 </td>
</tr>
'''[1:]

    def test_textarea(self):
        k = 'user.comment'
        with spec("returns (or prints) textarea tag."):
            ret = self.form_helper.textarea(k, 'Comment', 'Max 255 characters.')
            ok (ret) == r'''
<tr>
 <th>Comment</th>
 <td>
  <span><textarea name="user.comment">I have no interest in ordinary people!</textarea></span>
  <div class="desc"><em>(Max 255 characters.)</em></div>
 </td>
</tr>
'''[1:]
        with spec("if error exists then prints error message."):
            self.params[k] = ''
            self.errors[k] = 'Empty.'
            ret = self.form_helper.textarea(k, 'Comment', 'Max 255 characters.')
            ok (ret) == r'''
<tr>
 <th class="has-error">Comment</th>
 <td class="has-error">
  <span class="has-error"><textarea name="user.comment"></textarea></span>
  <div class="error-msg">Empty.</div>
  <div class="desc"><em>(Max 255 characters.)</em></div>
 </td>
</tr>
'''[1:]

    def test_select(self):
        k = 'user.weekday'
        with spec("returns (or prints) select tag and option tags."):
            ret = self.form_helper.select(k, 'Weekday', 'Optional.', items=WEEKDAYS, blank='--')
            ok (ret) == r'''
<tr>
 <th>Weekday</th>
 <td>
  <span><select name="user.weekday">
  <option value="">--</option>
  <option value="mon">Monday</option>
  <option value="tue">Tuesday</option>
  <option value="wed">Wednesday</option>
  <option value="thu">Thirsday</option>
  <option value="fri">Friday</option>
  <option value="sat" selected="selected">Saturday</option>
  <option value="sun">Sunday</option>
</select></span>
  <div class="desc"><em>(Optional.)</em></div>
 </td>
</tr>
'''[1:]
        with spec("if error exists then prints error message."):
            self.params[k] = ''
            self.errors[k] = 'Not selected.'
            ret = self.form_helper.select('user.weekday', 'Weekday', 'Optional.', items=WEEKDAYS, blank='--')
            ok (ret) == r'''
<tr>
 <th class="has-error">Weekday</th>
 <td class="has-error">
  <span class="has-error"><select name="user.weekday">
  <option value="">--</option>
  <option value="mon">Monday</option>
  <option value="tue">Tuesday</option>
  <option value="wed">Wednesday</option>
  <option value="thu">Thirsday</option>
  <option value="fri">Friday</option>
  <option value="sat">Saturday</option>
  <option value="sun">Sunday</option>
</select></span>
  <div class="error-msg">Not selected.</div>
  <div class="desc"><em>(Optional.)</em></div>
 </td>
</tr>
'''[1:]

    def test_radios(self):
        k = 'user.weekday'
        with spec("returns (or prints) radio button tags."):
            ret = self.form_helper.radios(k, 'Weekday', 'Optional.', items=WEEKDAYS, blank='--')
            ok (ret) == r'''
<tr>
 <th>Weekday</th>
 <td>
  <span><label><input type="radio" name="user.weekday" value="mon">Monday</label>
<label><input type="radio" name="user.weekday" value="tue">Tuesday</label>
<label><input type="radio" name="user.weekday" value="wed">Wednesday</label>
<label><input type="radio" name="user.weekday" value="thu">Thirsday</label>
<label><input type="radio" name="user.weekday" value="fri">Friday</label>
<label><input type="radio" name="user.weekday" value="sat" checked="checked">Saturday</label>
<label><input type="radio" name="user.weekday" value="sun">Sunday</label>
</span>
  <div class="desc"><em>(Optional.)</em></div>
 </td>
</tr>
'''[1:]
        with spec("if error exists then prints error message."):
            self.params[k] = ''
            self.errors[k] = 'Not choosed.'
            ret = self.form_helper.radios(k, 'Weekday', 'Optional.', items=WEEKDAYS, blank='--')
            ok (ret) == r'''
<tr>
 <th class="has-error">Weekday</th>
 <td class="has-error">
  <span class="has-error"><label><input type="radio" name="user.weekday" value="mon">Monday</label>
<label><input type="radio" name="user.weekday" value="tue">Tuesday</label>
<label><input type="radio" name="user.weekday" value="wed">Wednesday</label>
<label><input type="radio" name="user.weekday" value="thu">Thirsday</label>
<label><input type="radio" name="user.weekday" value="fri">Friday</label>
<label><input type="radio" name="user.weekday" value="sat">Saturday</label>
<label><input type="radio" name="user.weekday" value="sun">Sunday</label>
</span>
  <div class="error-msg">Not choosed.</div>
  <div class="desc"><em>(Optional.)</em></div>
 </td>
</tr>
'''[1:]

    def test__form_class_attr(self):
        with spec("if errmsg exists then returns class attr string"):
            ret = self.form_helper._form_class_attr("ERROR", {})
            ok (ret) == ' class="has-error"'
        with spec("if errmsg doesn't exist then returns empty string"):
            ret = self.form_helper._form_class_attr(None, {})
            ok (ret) == ''

    def test__form_control(self):
        def _control():
            return "<input />"
        with spec("if self.buf is specified then appends output to it"):
            buf = []
            fh = k8.FormHelper(self.params, self.errors, buf)
            ret = fh._form_control(_control, 'user.name', 'Name', None, {})
            ok (''.join(buf)) == r'''
<tr>
 <th>Name</th>
 <td>
  <span><input /></span>
 </td>
</tr>
'''[1:]
        with spec("if self.buf is specified then returns empty string"):
            ok (ret) == ''
        with spec("if self.buf is not specified then returns output string"):
            buf = []
            fh = k8.FormHelper(self.params, self.errors)
            ret = fh._form_control(_control, 'user.name', 'Name', None, {})
            ok (ret) == r'''
<tr>
 <th>Name</th>
 <td>
  <span><input /></span>
 </td>
</tr>
'''[1:]

    def test_to_hidden_tags(self):
        with spec("converts params into hidden tags."):
            expected = r'''
<input type="hidden" name="user.age" value="16" />
<input type="hidden" name="user.upload" value="" />
<input type="hidden" name="user.passwd" value="SOS" />
<input type="hidden" name="user.name" value="Haruhi" />
<input type="hidden" name="user.gender" value="F" />
<input type="hidden" name="user.comment" value="I have no interest in ordinary people!" />
<input type="hidden" name="user.weekday" value="sat" />
'''[1:]
            ret = self.form_helper.to_hidden_tags()
            def _to_lines(s):
                return set(list(s.splitlines(True)))
            ok (_to_lines(ret + "\n")) == _to_lines(expected)


if __name__ == '__main__':
    oktest.run()
