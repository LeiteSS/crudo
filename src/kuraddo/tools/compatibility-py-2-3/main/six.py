from __future__ import absolute_import

import functools
import itertools
import operator
import sys
import types

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
PY3DOT4 = sys.version_info[0:2] >= (3, 4)

if PY3:
  string_types = str
  integer_types = int
  class_types = type
  text_type = str
  binary_type = bytes

  MAXSIZE = sys.maxsize
else:
  string_types = basestring
  integer_types = (int, long)
  class_types = (type, types.ClassType)
  text_type = unicode
  binary_type = str

  if sys.platform.startswith("java"):
    MAXSIZE = int((1 << 31) - 1)
  else:
    class X(object):
      def __len__(self):
        return 1 << 31
    try:
      len(X())
    except OverflowError:
      MAXSIZE = int((1 << 31) - 1)
    else:
      MAXSIZE = int((1 << 63) - 1)
    del X

if PY3DOT4:
  from importlib.util import spec_from_loader
else:
  spec_from_loader = None

def _add_doc(func, doc):
  func.__doc__ = doc

def _import_module(name):
  """Import module, returning the module after the last dot."""
  __import__(name)
  return sys.modules[name]

class _LazyDescr(object):
  def __init__(self, name):
    self.name = name
  
  def __get__(self, obj, tp):
    result = self._resolve()
    setattr(obj, self.name, result)
    try:
      delattr(obj.__class__, self.name)
    except AttributeError:
      pass
    
    return result

class MovedModule(_LazyDescr):
  def __init__(self, name, old, new=None):
    super(MovedModule, self).__init__(name)

    if PY3:
      if new is None:
        new = name
      self.mod = new
    else:
      self.mod = old
  
  def _resolve(self):
    return _import_module(self.mod)
  
  def __getattribute__(self, attr):
    _module = self._resolve()
    value = getattr(_module, attr)
    setattr(self, attr, value)
    return value

# stopped in _LazyModule




  
