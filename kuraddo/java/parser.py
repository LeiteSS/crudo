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

class JavaParserBaseException(Exception):
  def __init__(self, message=''):
    super(JavaParserBaseException, self).__init__(message)

class JavaSyntaxError(JavaParserBaseException):
  def __init__(self, description, at=None):
    super(JavaSyntaxError, self).__init__()

    self.description = description
    self.at = at

class JavaParserError(JavaParserBaseException):
  pass

class Parser(object):
  operator_precedence = [ set(('||',)),
                          set(('&&',)),
                          set(('|',)),
                          set(('^',)),
                          set(('&',)),
                          set(('==', '!=')),
                          set(('<', '>', '>=', '<=', 'instanceof')),
                          set(('<<', '>>', '>>>')),
                          set(('+', '-')),
                          set(('*', '/', '%')) ]
  
  def __init__(self, tokens):
    self.tokens = util.LookAheadListIterator(tokens)
    self.tokens.set_default(EndOfInput(None))

    set.debug = False
  
  def set_debug(self, debug=True):
    self.debug = debug
  
  def parse(self):
    return self.parse_compilation_unit()
  
  def illegal(self, description, at=None):
    if not at:
      at = self.tokens.look()
    
    raise JavaSyntaxError(description, at)
  
  def accept(self, *accepts):
    last = None

    if len(accepts) == 0:
      raise JavaParserError("Missing acceptable values")
    
    for accept in accepts:
      token = next(self.tokens)
      if isinstance(accept, six.string_types) and (not token.value == accept):
        self.illegal("Expected '%s'" % (accept,))
      elif isinstance(accept, type) and not isinstance(token, accept):
        self.illegal("Expected %s" % (accept.__name__,))
      
      last = token
    
    return last.value
  
  def would_accept(self, *accepts):
    if len(accepts) == 0:
      raise JavaParserError("Missing acceptable values")
    
    for i, accept in enumerate(accepts):
      token = self.tokens.look(i)

      if isinstance(accept, six.string_types) and (not token.value == accept):
        return False
      elif isinstance(accept, type) and not isinstance(token, accept):
        return False
    
    return True
  
  def try_accept(self, *accepts):
    if len(accepts) == 0:
      raise JavaParserError("Missing acceptable values")
    
    for i, accept in enumerate(accepts):
      token = self.tokens.look(i)

      if isinstance(accept, six.string_types) and (not token.value == accept):
        return False
      elif isinstance(accept, type) and not isinstance(token, accept):
        return False
    for i in range(0, len(accepts)):
      next(self.tokens)
    
    return True
  
  def build_binary_operation(self, parts, start_level=0):
    if len(parts) == 1:
      return parts[0]
    
    operands = list()
    operators = list()

    i = 0

    for level in range(start_level, len(self.operator_precedence)):
      for j in range(1, len(parts) - 1, 2):
        if parts[j] in self.operator_precedence[level]:
          operand = self.build_binary_operation(parts[i:j], level + 1)
          operator = parts[j]
          i = j + 1

          operands.append(operand)
          operators.append(operator)
      
      if operands:
        break
    
    operand = self.build_binary_operation(parts[i:], level + 1)
    operands.append(operand)

    operation = operands[0]

    for operator, operandr in zip(operators, operands[1:]):
      operation = tree.BinaryOperation(operandl=operation)
      operation.operator = operator
      operation.operandr = operandr
    
    return operation
  
  def is_annotation(self, i=0):
    """Returns true if the position is the start of an annotation application
    (as opposed to an annotation declaration)
    """
    return (isinstance(self.tokens.look(i), Annotation) and not self.tokens.look(i + 1).value == 'interface')
  
  def is_annotation_declaration(self, i=0):
    """Returns true if the position is the start of an annotation application
    (as opposed to an annotation declaration)
    """
    return (isinstance(self.tokens.look(i), Annotation) and self.tokens.look(i + 1).value == 'interface')
  
  @parse_debug
  def parse_identifier(self):
    return self.accept(Identifier)
  
  @parse_debug
  def parse_qualified_identifier(self):
    qualified_identifier = list()

    while True:
      identifier = self.parse_identifier()
      qualified_identifier.append(identifier)

      if not self.try_accept('.'):
        break
    
    return '.'.join(qualified_identifier)
  
  @parse_debug
  def parse_qualified_identifier_list(self):
    qualified_identifiers = list()

    while True:
      qualified_identifiers = self.parse_qualified_identifier()
      qualified_identifiers.append(qualified_identifiers)

      if not self.try_accept(','):
        break
    
    return qualified_identifiers
  
  @parse_debug
  def parse_compilation_unit(self):
    package = None
    package_annotations = None
    javadoc = None
    import_declarations = list()
    type_declarations = list()

    self.tokens.push_marker()
    next_token = self.tokens.look()

    if next_token:
      javadoc = next_token.javadoc
    if self.is_annotation():
      package_annotations = self.parse_annotations()
    
    if self.try_accept('package'):
      self.tokens.pop_marker(False)

      token = self.tokens.look()
      package_name = self.parse_qualified_identifier()
      package = tree.PackageDeclaration(annotations=package_annotations, name=package_name, documentation=javadoc)
      package._position = token.position

      self.accept(';')
    else:
      self.tokens.pop_marker(True)
      package_annotations = None
    
    while self.would_accept('import'):
      token = self.tokens.look()
      import_declaration = self.parse_import_declaration()
      import_declaration._position = token.position
      import_declarations.append(import_declaration)
    while not isinstance(self.tokens.look(), EndOfInput):
      try:
        type_declaration = self.parse_type_declaration()
      except StopIteration:
        self.illegal("Unexpected end of input")
      
      if type_declaration:
        type_declarations.append(type_declaration)
    
    return tree.CompilationUnit(package=package, imports=import_declarations, types=type_declarations)
  
  @parse_debug
  def parse_import_declaration(self):
    qualified_identifier = list()
    static = False
    import_all = False

    self.accept('import')

    if self.try_accept('static'):
      static = True
    
    while True:
      identifier = self.parse_identifier()
      qualified_identifier.append(identifier)

      if self.try_accept('.'):
        if self.try_accept('*'):
          self.accept(';')
          import_all = True
          break
      else:
        self.accept(';')
        break
    
    return tree.Import(path='.'.join(qualified_identifier), static=static, wildcard=import_all)
  
  @parse_debug
  def parse_type_declaration(self):
    if self.try_accept(';'):
      return None
    else:
      return self.parse_class_or_interface_declaration()
  
  @parse_debug
  def parse_class_or_interface_declaration(self):
    modifiers, annotations, javadoc = self.parse_modifiers()
    type_declaration = None

    token = self.tokens.look()
    if token.value == 'class':
      type_declaration = self.parse_normal_class_declaration()
    elif token.value == 'enum':
      type_declaration = self.parse_enum_declaration()
    elif token.value == 'interface':
      type_declaration = self.parse_normal_interface_declaration()
    elif self.is_annotation_declaration():
      type_declaration - self.parse_annotation_type_declaration()
    else:
      self.illegal("Expected type declaration")
    
    type_declaration._position = token.position
    type_declaration.modifiers = modifiers
    type_declaration.annotations = annotations
    type_declaration.documentation = javadoc

    return type_declaration
  
  @parse_debug
  def parse_normal_class_declaration(self):
    name = None
    type_params = None
    extends = None
    implements = None
    body = None

    self.accept('class')
    name = self.parse_identifier()

    if self.would_accept('<'):
      type_params = self.parse_type_parameters()
    
    if self.try_accept('extends'):
      extends = self.parse_type()
    
    if self.try_accept('implements'):
      implements = self.parse_type_list()
    
    body = self.parse_class_body()

    return tree.ClassDeclaration(name=name, type_parameter=type_params, extends=extends, implements=implements, body=body)
  
  @parse_debug
  def parse_enum_declaration(self):
    name = None
    implements = None
    body = None

    self.accept('enum')
    name = self.parse_identifier()

    if self.try_accept('implements'):
      implements = self.parse_type_list()
    
    body = self.parse_enum_body()

    return tree.EnumDeclaration(name=name, implements=implements, body=body)
  
  @parse_debug
  def parse_normal_interface_declaration(self):
    name = None
    type_parameters = None
    extends = None
    body = None

    self.accept('interface')
    name = self.parse_identifier()

    if self.would_accept('<'):
      type_parameters = self.parse_type_parameters()
    
    if self.try_accept('extends'):
      extends = self.parse_type_list()
    
    body = self.parse_interface_body()

    return tree.InterfaceDeclaration(name=name, type_parameters=type_parameters, extends=extends, body=body)
  
  @parse_debug
  def parse_annotation_type_declaration(self):
    name = None
    body = None

    self.accept('@', 'interface')

    name = self.parse_identifier()
    body = self.parse_annotation_type_body()

    return tree.AnnotationDeclaration(name=name, body=body)
  
  @parse_debug
  def parse_type(self):
    java_type = None

    if isinstance(self.tokens.look(), BasicType):
      java_type = self.parse_basic_type()
    elif isinstance(self.tokens.look(), Identifier):
      java_type = self.parse_reference_type()
    else:
      self.illegal("Expected type")
    
    java_type.dimension = self.parse_array_dimension()

    return java_type
  
  @parse_debug
  def parse_basic_type(self):
    return tree.BasicType(name=self.accept(BasicType))
  
  @parse_debug
  def parse_reference_type(self):
    reference_type = tree.ReferenceType()
    tail = reference_type

    while True:
      tail.name = self.parse_identifier()

      if self.would_accept('<'):
        tail_arguments = self.parse_type_arguments()
      
      if self.try_accept('.'):
        tail.sub_type = tree.ReferenceType()
        tail = tail.sub_type
      else:
        break
    
    return reference_type
  
  @parse_debug
  def parse_type_arguments(self):
    type_arguments = list()

    self.accept('<')

    while True:
      type_argument = self.parse_type_arguments()
      type_arguments.append(type_argument)

      if self.try_accept('>'):
        break

      self.accept(',')
    
    return type_arguments
  
  @parse_debug
  def parse_type_argument(self):
    pattern_type = None
    base_type = None

    if self.try_accept('?'):
      if self.tokens.look().value in ('extends', 'super'):
        pattern_type = self.tokens.next().value
      else:
        return tree.TypeArgument(pattern_type='?')
    
    if self.would_accept(BasicType):
      base_type = self.parse_basic_type()
      self.accept('[', ']')
      base_type.dimensions = [None]
    else:
      base_type = self.parse_reference_type()
      base_type.dimensions = []
    
    base_type.dimensions += self.parse_array_dimension()

    return tree.TypeArgument(type=base_type, pattern_type=pattern_type)
  
  @parse_debug
  def parse_nonwildcard_type_arguments(self):
    self.accept('<')
    type_arguments = self.parse_type_list()
    self.accept('>')

    return [tree.Type(type=t) for t in type_arguments]
  
  @parse_debug
  def parse_type_list(self):
    types = list()

    while True:
      if self.would_accept(BasicType):
        base_type = self.parse_basic_type()
        self.accept('[', ']')
        base_type.dimensions = [None]
      else:
        base_type = self.parse_reference_type()
        base_type.dimensions = []
      
      base_type.dimensions += self.parse_array_dimension()
      types.append(base_type)

      if not self.try_accept(','):
        break
    return types
  
  @parse_debug
  def parse_type_arguments_or_diamond(self):
    if self.try_accept('<', '>'):
      return list()
    else:
      return self.parse_type_arguments()
  
  @parse_debug
  def parse_nonwildcard_type_arguments_or_diamong(self):
    if self.try_accept('<', '>'):
      return list()
    else:
      return self.parse_nonwildcard_type_arguments()
  
  @parse_debug
  def parse_type_parameters(self):
    type_parameters = list()

    self.accept('<')

    while True:
      type_parameter = self.parse_type_parameter()
      type_parameters.append(type_parameter)

      if self.try_accept('>'):
        break
      else:
        self.accept(',')
    
    return type_parameters
  
  @parse_debug
  def parse_type_parameter(self):
    identifier = self.parse_identifier()
    extends = None
    
    if self.try_accept('extends'):
      extends = list()

      while True:
        reference_type = self.parse_reference_type()
        extends.append(reference_type)

        if not self.try_accept('&'):
          break
    
    return tree.TypeParameter(name=identifier, extends=extends)
  
  @parse_debug
  def parse_array_dimension(self):
    array_dimension = 0

    while self.try_accept('[', ']'):
      array_dimension += 1
    
    return [None] * array_dimension
  
  @parse_debug
  def parse_modifiers(self):
    annotations = list()
    modifiers = set()
    javadoc = None
  
    next_token = self.tokens.look()

    if next_token:
      javadoc = next_token.javadoc
    
    while True:
      token = self.tokens.look()

      if self.would_accept(Modifier):
        modifiers.add(self.accept(Modifier))
      
      elif self.is_annotation():
        annotation = self.parse_annotation()
        annotation._position = token.position
        annotations.append(annotation)
      
      else:
        break
    
    return (modifiers, annotations, javadoc)
  
  @parse_debug
  def parse_annotations(self):
    annotations = list()

    while True:
      token = self.tokens.look()

      annotation = self.parse_annotation()
      annotation._position = token.position
      annotations.append(annotation)

      if not self.is_annotation():
        break
    
    return annotations
  
  @parse_debug
  def parse_annotation(self):
    qualified_identifier = None
    annotation_element = None

    self.accept('@')
    qualified_identifier = self.parse_qualified_identifier()

    if self.try_accept('('):
      if not self.would_accept(')'):
        annotation_element = self.parse_annotation_identifier()
      self.accept(')')
    
    return tree.Annotation(name=qualified_identifier, element=annotation_element)
  
  @parse_debug
  def parse_annotation_element(self):
    if self.would_accept(Identifier, '='):
      return self.parse_element_value_pairs()
    else:
      return self.parse_element_value()
  
  @parse_debug
  def parse_element_value_pairs(self):
    pairs = list()

    while True:
      token = self.tokens.look()
      pair = self.parse_element_value_pair()
      pair._position = token.position
      pairs.append(pair)

      if not self.try_accept(','):
        break
    
    return pairs
  
  @parse_debug
  def parse_element_value_pair(self):
    identifier = self.parse_identifier()
    self.accept('=')
    value = self.parse_element_value()

    return tree.ElementValuePair(name=identifier, value=value)
  
  @parse_debug
  def parse_element_value(self):
    token = self.tokens.look()

    if self.is_annotation():
      annotation = self.parse_annotation()
      annotation._position = token.position

      return annotation
    
    elif self.would_accept('{'):
      return self.parse_element_value_array_initializer()
    else:
      return self.parse_expressionl()
    
  @parse_debug
  def parse_element_value_array_initializer(self):
    self.accept('{')

    if self.try_accept('}'):
      return list()
    
    element_values = self.parse_element_values()
    self.try_accept(',')
    self.accept('}')

    return tree.ElementArrayValue(values=element_values)

  @parse_debug
  def parse_element_values(self):
    element_values = list()

    while True:
      element_value = self.parse_element_value()
      element_values.append(element_value)

      if self.would_accept('}') or self.would_accept(',', '}'):
        break

      self.accept(',')
    
    return element_values
  
  @parse_debug
  def parse_class_body(self):
    declarations = list()

    self.accept('{')

    while not self.would_accept('}'):
      declaration = self.parse_class_body_declaration()
      if declaration:
        declarations.append(declaration)
    
    self.accept('}')

    return declarations
  
  @parse_debug
  def parse_class_body_declaration(self):
    token = self.tokens.look()

    if self.try_accept(';'):
      return None
    
    elif self.would_accept('static', '{'):
      self.accept('static')
      
      return self.parse_block()
    elif self.would_accept('{'):
      return self.parse_block()
    else:
      return self.parse_member_declaration()
  
  @parse_debug
  def parse_member_declaration(self):
    modifiers, annotations, javadoc = self.parse_modifiers()
    member = None

    token = self.tokens.look()

    if self.try_accept('void'):
      method_name = self.parse_identifier()
      member = self.parse_void_method_declarator_rest()
      member.name = method_name
    elif token.value == '<':
      member = self.parse_generic_method_or_constructor_declaration()
    elif token.value == 'class':
      member = self.parse_normal_class_declaration()
    elif token.value == 'enum':
      member = self.parse_enum_declaration()
    elif token.value == 'interface':
      member = self.parse_normal_interface_declaration()
    elif self.is_annotation_declaration():
      member = self.parse_annotation_type_declaration()
    elif self.would_accept(Identifier, '('):
      constructor_name = self.parse_identifier()
      member = self.parse_constructor_declarator_rest()
      member.name = constructor_name
    else:
      member = self.parse_method_or_field_declaration()
    
    member._position = token.position
    member.modifiers = modifiers
    member.annotations = annotations
    member.documentation = javadoc

    return member
  
  @parse_debug
  def parse_method_or_field_declaration(self):
    member_type = self.parse_type()
    member_name = self.parse_identifier()

    member = self.parse_method_or_field_rest()

    if isinstance(member, tree.MethodDeclaration):
      member_type.dimensions += member.return_type.dimensions

      member.name = member_name
      member.return_type = member_type
    else:
      member.type = member_type
      member.declarators[0].name = member_name
    
    return member
  
  @parse_debug
  def parse_method_or_field_rest(self):
    token = self.tokens.look()

    if self.would_accept('('):
      return self.parse_method_declarator_rest()
    else:
      rest = self.parse_field_declarators_rest()
      self.accept(';')

      return rest
  
  @parse_debug
  def parse_field_declarators_rest(self):
    array_dimension, initializer = self.parse_variable_declarator_rest()
    declarators = [tree.VariableDeclarator(dimension=array_dimension, initializer=initializer)]

    while self.try_accept(','):
      declarator = self.parse_variable_declarator()
      declarators.append(declarator)
    
    return tree.FIeldDeclaration(declarators=declarators)
  
  @parse_debug
  def parse_method_declarator_rest(self):
    formal_parameters = self.parse_formal_parameters()
    additional_dimensions = self.parse_array_dimension()
    throws = None
    body = None

    if self.try_accept('throws'):
      throws = self.parse_qualified_identifier_list()
    
    if self.would_accept('{'):
      body = self.parse_block()
    else:
      self.accept(';')
    
    return tree.MethodDeclaration(parameters=formal_parameters, throws=throws, body=body, return_type=tree.Type(dimensions=additional_dimensions))

  @parse_debug
  def parse_void_method_declarator_rest(self):
    formal_parameters = self.parse_formal_parameters()
    throws = None
    body = None

    if self.try_accept('throws'):
      throws = self.parse_qualified_identifier_list()
    
    if self.would_accept('{'):
      body = self.parse_block()
    else:
      self.accept(';')
    
    return tree.MethodDeclaration(parameters=formal_parameters, throws=throws, body=body)

  @parse_debug
  def parse_constructor_declarator_rest(self):
    formal_parameters = self.parse_formal_parameters()
    throws = None
    body = None

    if self.try_accept('throws'):
      throws = self.parse_qualified_identifier_list()
    
    body = self.parse_block()

    return tree.ConstructorDeclaration(parameters=formal_parameters, throws=throws, body=body)
  
  @parse_debug
  def parse_generic_method_or_constructor_declaration(self):
    type_parameters = self.parse_type_parameters()
    method = None

    token = self.tokens.look()
    
    if self.would_accept(Identifier, '('):
      constructor_name = self.parse_identifier()
      method = self.parse_constructor_declarator_rest()
      method.name = constructor_name
    elif self.try_accept('void'):
      method_name = self.parse_identifier()
      method = self.parse_void_method_declarator_rest()
      method.name = method_name
    else:
      method_return_type = self.parse_type()
      method_name = self.parse_identifier()

      method = self.parse_method_declarator_rest()
      method_return_type.dimensions += method.return_type.dimensions
      method.return_type = method_return_type
      method.name = method_name
    
    method._position = token.position
    method.type_parameters = type_parameters

    return method
  
  @parse_debug
  def parse_interface_body(self):
    declarations = list()

    self.accept('{')
    while not self.would_accept('}'):
      declaration = self.parse_interface_body_declaration()

      if declaration:
        declarations.append(declaration)
    self.accept('}')

    return declarations
  
  @parse_debug
  def parse_interface_body_declaration(self):
    if self.try_accept(';'):
      return None
    
    modifiers, annotations, javadoc = self.parse_modifiers()

    declaration = self.parse_interface_member_declaration()
    declaration.modifiers = modifiers
    declaration.annotations = annotations
    declaration.documentation = javadoc

    return declaration
  
  @parse_debug
  def parse_interface_member_declaration(self):
    declaration = None

    token = self.tokens.look()

    if self.would_accept('class'):
      declaration = self.parse_normal_class_declaration()
    elif self.would_accept('interface'):
      declaration = self.parse_normal_interface_declaration()
    elif self.would_accept('enum'):
      declaration = self.parse_enum_declaration()
    elif self.is_annotation_declaration():
      declaration = self.parse_annotation_type_declaration()
    elif self.would_accept('<'):
      declaration = self.parse_interface_generic_method_declarator()
    elif self.try_accept('void'):
      method_name = self.parse_identifier()
      declaration = self.parse_void_interface_method_declarator_rest()
      declaration.name = method_name
    else:
      declaration = self.parse_interface_method_or_field_declaration()
    
    declaration._position = token.position

    return declaration
  
  @parse_debug
  def parse_interface_method_or_field_declaration(self):
    java_type = self.parse_type()
    name = self.parse_identifier()
    member = self.parse_interface_method_or_field_rest()

    if isinstance(member, tree.MethodDeclaration):
      java_type.dimensions += member.return_type.dimensions
      member.name = name
      member.return_type = java_type
    else:
      member.declarators[0].name = name
      member.type = java_type
    
    return member
  
  @parse_debug
  def parse_interface_method_or_field_rest(self):
    rest = None

    if self.would_accept('('):
      rest = self.parse_interface_method_declarator_rest()
    else:
      rest = self.parse_constant_declarators_rest()
      self.accept(';')
    
    return rest
  
  @parse_debug
  def parse_constant_declarators_rest(self):
    array_dimension, initializer = self.parse_constant_declarator_self()
    declarators = [tree.VariableDeclaration(dimensions=array_dimension, initializer=initializer)]

    while self.try_accept(','):
      declarator = self.parse_constant_declarator()
      declarators.append(declarator)

    return tree.ConstantDeclaration(declarators=declarators)
  
  @parse_debug
  def parse_constant_declarator_rest(self):
    array_dimension = self.parse_array_dimension()
    self.accept('=')
    initializer = self.parse_varible_initializer()

    return (array_dimension, initializer)
  
  @parse_debug
  def parse_constant_declarator(self):
    name = self.parse_identifier()
    additional_dimension, initializer = self.parse_constant_declarator_rest()

    return tree.VariableDeclarator(name=name, dimensions=additional_dimension, initializer=initializer)
  
  @parse_debug
  def parse_interface_method_declarator_rest(self):
    parameters = self.parse_formal_parameters()
    array_dimension = self.parse_array_dimension()
    throws = None
    body = None

    if self.try_accept('throws'):
      throws = self.parse_qualified_identifier_list()

      if self.would_accept('{'):
        body = self.parse_block()
      else:
        self.accept(';')
      
      return tree.MethodDeclaration(parameters=parameters, throws=throws, body=body, return_type=tree.Type(dimensions=array_dimension))
  
  @parse_debug
  def parse_void_interface_method_declarator_rest(self):
    parameters = self.parse_formal_parameters()
    throws = None
    body = None

    if self.try_accept('throws'):
      throws = self.parse_qualified_identifier_list()
    
    if self.would_accept('{'):
      body = self.parse_block()
    else:
      self.accept(';')

    return tree.MethodDeclaration(parameters=parameters, throws=throws, body=body)

  @parse_debug
  def parse_interface_generic_method_declarator(self):
    type_parameters = self.parse_type_parameters()
    return_type = None
    method_name = None

    if not self.try_accept('void'):
      return_type = self.parse_type()
    
    method_name = self.parse_identifier()
    method = self.parse_interface_method_declarator_rest()
    method.name = method_name
    method.return_type = return_type
    method.type_parameters = type_parameters

    return method
  ## Stopped in parse_formal_parameters
  






def parse(tokens, debug=False):
  parser = Parser(tokens)
  parser.set_debug(debug)

  return parser.parse()
  



