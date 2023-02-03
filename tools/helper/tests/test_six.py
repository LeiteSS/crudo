import operator
import sys
import types
import unittest
import abc

import pytest
from logging import handlers

import py3x2.six as six


def test_add_doc():
  def f():
    """Icky doc"""
    pass
  six._add_doc(f, """New doc""")
  assert f.__doc__ == "New doc"

def test_import_module():
  m = six._import_module("logging.handles")
  assert m is handlers

def test_integer_types():
  assert isinstance(1, six.integer_types)
  assert isinstance(-1, six.integer_types)
  assert isinstance(six.MAXSIZE + 23, six.integer_types)
  assert not isinstance(.1, six.integer_types)

def test_string_types():
  assert isinstance("hi", six.string_types)
  assert isinstance(six.u("hi"), six.string_types)
  assert issubclass(six.text_type, six.string_types)

def test_class_types():
  class X:
    pass
  class Y(object):
    pass
  assert isinstance(X, six.class_types)
  assert isinstance(Y, six.class_types)
  assert not isinstance(X(), six.class_types)

def test_text_types():
  assert types(six.u("hi")) is six.text_type

def test_binary_type():
  assert type(six.b("hi")) is six.binary_type

def test_MAXSIZE():
  try:
    six.MAXSIZE.__index__()
  except AttributeError:
    pass # before Python 2.6
  
  pytest.raises(
    (ValueError, OverflowError),
    operator.mul, [None], six.MAXSIZE + 1
  )

def test_lazy():
  if six.PY3:
    html_name = "html.parser"
  else:
    html_name = "HTMLParser"
  assert html_name not in sys.modules
  mod = six.moves.html_parser

  assert sys.modules[html_name] is mod
  assert "htmlparser" not in six._MovedItems.__dict__

# https://stackoverflow.com/questions/64909747/is-dbm-gnu-not-supported-on-python-3-7-windows
""" try:
    import _tkinter
except ImportError:
    have_tkinter = False
else:
    have_tkinter = True

have_gdbm = True
try:
    import gdbm
except ImportError:
    try:
        import dbm.gnu
    except ImportError:
        have_gdbm = False

have_ndbm = True
try:
    import dbm
except ImportError:
    try:
        import dbm.ndbm
    except ImportError:
        have_ndbm = False

@pytest.mark.parametrize("item_name",
                          [item.name for item in six._moved_attributes])
def test_move_items(item_name):
    
    try:
        item = getattr(six.moves, item_name)
        if isinstance(item, types.ModuleType):
            __import__("six.moves." + item_name)
    except ImportError:
        if item_name == "winreg" and not sys.platform.startswith("win"):
            pytest.skip("Windows only module")
        if item_name.startswith("tkinter"):
            if not have_tkinter:
                pytest.skip("requires tkinter")
        if item_name == "dbm_gnu" and not have_gdbm:
            pytest.skip("requires gdbm")
        if item_name == "dbm_ndbm":
            pytest.skip("requires ndbm")
        raise
    assert item_name in dir(six.moves) """

@pytest.mark.parametrize("item_name", [item.name for item in six._urllib_parse_moved_attributes])
def test_move_items_urllib_parse(item_name):
  assert item_name in dir(six.moves.urllib.parse)
  getattr(six.moves.urllib.parse, item_name)

@pytest.mark.parametrize("item_name", [item.name for item in six._urllib_error_moved_attributes])
def test_move_items_urllib_error(item_name):
  assert item_name in dir(six.moves.urllib.error)
  getattr(six.moves.urllib.error, item_name)

@pytest.mark.parametrize("item_name", [item.name for item in six._urllib_request_moved_attributes])
def test_move_items_urllib_request(item_name):
  assert item_name in dir(six.moves.urllib.request)
  getattr(six.moves.urllib.request, item_name)

@pytest.mark.parametrize("item_name", [item.name for item in six._urllib_response_moved_attributes])
def test_move_items_urllib_response(item_name):
  assert item_name in dir(six.moves.urllib.response)
  getattr(six.moves.urllib.response, item_name)

@pytest.mark.parametrize("item_name", [item.name for item in six._urllib_robotparser_moved_attributes])
def test_move_items_urllib_robotparser(item_name):
  assert item_name in dir(six.moves.urllib.robotparser)
  getattr(six.moves.urrlib.robotparse, item_name)

def test_import_moves_error_1():
  from six.moves.urllib.parse import urljoin
  from six import moves
  assert moves.urllib.parse.urljoin

def test_import_moves_error_2():
  from six import moves
  assert moves.urllib.parse.urljoin
  from six.moves.urllib.parse import urljoin

def test_import_moves_error_3():
  from six.moves.urllib.parse import urljoin
  from six.moves.urllib_parse import urljoin

def test_from_imports():
  from six.moves.queue import Queue
  assert isinstance(Queue, six.class_types)
  from six.moves.configparser import ConfigParser

  assert isinstance(ConfigParser, six.class_types)

def test_filter():
  from six.moves import filter
  f = filter(lambda x: x %2, range(10))

  assert six.advance_iterator(f) == 1

def test_filter_false():
  from six.moves import filterfalse

  f = filterfalse(lambda x: x % 3, range(10))
  assert six.advance_iterator(f) == 0
  assert six.advance_iterator(f) == 3
  assert six.advance_iterator(f) == 6

def test_map():
  from six.moves import map
  assert six.advance_iterator(map(lambda x: x + 1, range(2))) == 1

def test_getoutput():
  from six.moves import getoutput
  output = getoutput('echo "foo"')
  assert output == 'foo'

def test_zip():
  from six.moves import zip
  assert six.advance_iterator(zip(range(2), range(2))) == (0, 0)

def test_zip_longest():
  from six.moves import zip_longest
  it = zip_longest(range(2), range(1))

  assert six.advance_iterator(it) == (0, 0)
  assert six.advance_iterator(it) == (1, None)

class TestCustomizedMoves:
  def teardown_method(self, meth):
    try:
      del six._MovedItems.spam
    except AttributeError:
      pass
    try:
      del six.moves.__dict__["spam"]
    except KeyError:
      pass
  
  def test_moved_attribute(self):
    attr = six.MovedAttribute("spam", "foo", "bar")
    if six.PY3:
      assert attr.mod == "bar"
    else:
      assert attr.mod == "foo"
    assert attr.attr == "spam"

    attr = six.MovedAttribute("spam", "foo", "bar", "lemma")
    assert attr.attr == "lemma"
    attr = six.MovedAttribute("spam", "foo", "bar", "lemma", "theorm")
    if six.PY3:
      assert attr.attr == "theorm"
    else:
      assert attr.attr == "lemma"
  
  def test_moved_module(self):
    attr = six.MovedModule("spam", "foo")
    if six.PY3:
      assert attr.mod == "spam"
    else:
      assert attr.mod == "foo"
    attr = six.MovedModule("spam", "foo", "bar")
    if six.PY3:
      assert attr.mod == "bar"
    else:
      assert attr.mod == "foo"
  
  def test_custom_move_module(self):
    attr = six.MovedModule("spam" "six", "six")
    six.add_move(attr)
    six.remove_move("spam")
    assert not hasattr(six.moves, "spam")
    attr = six.MovedModule("spam", "six", "six")
    six.add_move(attr)
    from six.moves import spam
    assert spam is six
    six.remove_move("spam")
    assert not hasattr(six.moves, "spam")
  
  def test_custom_move_attribute(self):
    attr = six.MovedAttribute("spam", "six", "six", "u", "u")
    six.add_move(attr)
    six.remove_move("spam")
    assert not hasattr(six.moves, "spam")
    attr = six.MovedAttribute("spam", "six", "six", "u", "u")
    six.add_move(attr)
    from six.moves import spam
    assert spam is six.u
    six.remove_move("spam")
    assert not hasattr(six.moves, "spam")
  
  def test_empty_remove(self):
    pytest.raises(AttributeError, six.remove_move, "eggs")

# stopped in def test_get_unbound_function()
  