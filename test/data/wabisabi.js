/// # -*- coding: utf-8 -*-

///
/// very small DOM builder using wabi-sabi style
///
/// Example:
///
///     var a  = dom(["a", {href: "/link"}, "Link"]);
///     console.log(a);
///         //=> <a href="/link">Link</a>
///
///     var ul = dom(
///       ["ul#main.foo.bar", {style: "float:left"}
///       , ["li", ["a", "AAA"]]
///       , ["li", ["a", "BBB"]]
///       , ["li.active", ["a", "CCC"]]
///       ]
///     );
///     console.log(ul);
///         //=> <ul id="main" class="foo bar" style="float:left">
///         //     <li><a>AAA</a></li>
///         //     <li><a>BBB</a></li>
///         //     <li class="active"><a>CCC</a></li>
///         //   </ul>
///
/// License: MIT-License
///

"use strict";


function dom(arr) {
  /// element
  /// (ex: span#foo.bar.baz => <span id="foo" class="bar baz">)
  var tag = arr[0], id = null, cls = null;
  var m = tag.match(/^([-\w]+)(?:\#([-\w]+))?(?:\.(.*))?/);
  if (m) { tag = m[1]; id = m[2]; cls = m[3]; }
  var el = document.createElement(tag);
  if (id) { el.id = id; }
  if (cls) { el.className = cls.replace('.', ' '); }
  /// attributes
  var attrs = arr[1];
  if (attrs && typeof attrs === 'object' && ! (attrs instanceof Array)) {
    for (var k in attrs) {
      var v = attrs[k];
      if (v == null) {
        // pass
      } else if (v === true || v === false) {
        el[k] = v;              // set as property
      } else {
        el.setAttribute(k, v);  // set as attribute
      }
    }
  } else {
    attrs = null;
  }
  /// children
  for (var i = attrs ? 2 : 1, n = arr.length; i < n; i++) {
    var x = arr[i];
    var t = typeof x;
    var c;
    if (x == null || x === "")   { c = null; }
    else if (t === "string" || t === "number" || t === "boolean")
                                 { c = document.createTextNode(x); }
    else if (t === "function")   { c = dom(x(el)); } // TODO: what is the best?
    else if (x instanceof Array) { c = x.length ? dom(x) : null; }
    else if (x instanceof Node)  { c = x; }
    else                         { c = document.createTextNode(x); } // should throw error?
    if (c) { el.appendChild(c); }
  }
  /// special operation!
  if (tag === "a" && ! el.href) {
    el.href = "javascript:undefined";
  }
  ///
  return el;
}
