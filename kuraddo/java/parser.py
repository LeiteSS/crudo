import tools.helper.py3x2.six as six

from . import util
from . import tree

from .tokenizer import (
  EndOfInput, 
  Keyword, 
  Modifier, 
  BasicType, 
  Identifier, 
  Annotation, 
  Literal, 
  Operator, 
  JavaToken
)

ENABLE_DEBUG_SUPPORT = False

def parse_debug(method):
  global ENABLE_DEBUG_SUPPORT

  if ENABLE_DEBUG_SUPPORT:
    def _method(self):
      if not hasattr(self, 'recursion_depth'):
        self.recursion_depth = 0
      
      if self.debug:
        depth = "%02d" % (self.recursion_depth,)
        token = six.text_type(self.tokens.look())
        start_value = self.tokens.look().value
        name = method.__name__
        sep = ("-" * self.recursion_depth)
        e_message = ""

        print("%s %s> %s (%s)" % (depth, sep, name, token))

        self.recursion_depth += 1

        try:
          r.method(self)
        except JavaSyntaxError as e:
          e_message = e.description
          raise
        except Exception as e:
          e_message = six.text_type(e)
          raise
        finally:
          token = six.text_type(self.tokens.last())
          print("%s <%s %s(%s, %s) %s" % (depth, sep, name, start_value, token, e_message))
          self.recursion_depth -= 1
      else:
        self.recursion_depth += 1
        try:
          r = method(self)
        finally:
          self.recursion_depth -= 1
      
      return _method
  else:
    return method

# stopped in Parsing Exception