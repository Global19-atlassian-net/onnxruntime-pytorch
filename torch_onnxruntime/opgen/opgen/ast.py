# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import sys
import io
from typing import TextIO
from enum import Enum
from opgen.lexer import TokenKind, Token

class Node(object):
  def __init__(self):
    self.tokens = []

  def write(self, writer: TextIO):
    raise NotImplementedError(self.write)

  def __str__(self):
    writer = io.StringIO()
    self.write(writer)
    return writer.getvalue()

#region Syntax List

class SyntaxListMember(Node):
  def __init__(self, member: Node, trailing_separator: Token):
    super().__init__()
    self.member = member
    self.trailing_separator = trailing_separator

  def write(self, writer: TextIO):
    self.member.write(writer)
    if self.trailing_separator:
      writer.write(self.trailing_separator.value)
      writer.write(" ")

class SyntaxList(Node):
  open_token: Token
  members: [SyntaxListMember]
  close_token: Token

  def __init__(self):
    super().__init__()
    self.open_token = None
    self.members = []
    self.close_token = None

  def __iter__(self):
    return self.members.__iter__()
  
  def __getitem__(self, key):
    return self.members.__getitem__(key)
  
  def __len__(self):
    return len(self.members)

  def append(self, member: Node, trailing_separator: Token):
    self.members.append(SyntaxListMember(member, trailing_separator))

  def write(self, writer: TextIO):
    if self.open_token:
      writer.write(self.open_token.value)
    for member in self.members:
      member.write(writer)
    if self.close_token:
      writer.write(self.close_token.value)

#endregion

#region Expressions

class Expression(Node): pass

class LiteralExpression(Expression):
  def __init__(self, token: Token):
    super().__init__()
    self.token = token

  def write(self, writer: TextIO):
    writer.write(self.token.value)

class ArrayExpression(Expression):
  def __init__(self, elements: SyntaxList):
    self.elements = elements

#endregion

#region Types

class Type(Node): pass

class ExpressionType(Type):
  def __init__(self, expression: Expression):
    super().__init__()
    self.expression = expression

  def write(self, writer: TextIO):
    self.expression.write(writer)

class ConcreteType(Type):
  def __init__(self, identifier_token: Token):
    super().__init__()
    self.identifier_token = identifier_token

  def write(self, writer: TextIO):
    writer.write(self.identifier_token.value)

class ConstType(Type):
  def __init__(self, const_token: Token, inner_type: Type):
    super().__init__()
    self.const_token = const_token
    self.inner_type = inner_type

  def write(self, writer: TextIO):
    writer.write(self.const_token.value)
    writer.write(" ")
    self.inner_type.write(writer)

class ReferenceType(Type):
  def __init__(self, inner_type: Type, reference_token: Token):
    super().__init__()
    self.inner_type = inner_type
    self.reference_token = reference_token

  def write(self, writer: TextIO):
    self.inner_type.write(writer)
    writer.write(self.reference_token.value)

class ModifiedType(Type):
  def __init__(self, base_type: Type):
    super().__init__()
    self.base_type = base_type

class OptionalType(ModifiedType):
  def __init__(self, base_type: Type, token: Token):
    super().__init__(base_type)
    self.token = token

  def write(self, writer: TextIO):
    self.base_type.write(writer)
    writer.write(self.token.value)

class ArrayType(ModifiedType):
  def __init__(
    self,
    base_type: Type,
    open_token: Token,
    length_token: Token,
    close_token: Token):
    super().__init__(base_type)
    self.open_token = open_token
    self.length_token = length_token
    self.close_token = close_token

  def write(self, writer: TextIO):
    self.base_type.write(writer)
    writer.write(self.open_token.value)
    if self.length_token:
      writer.write(self.length_token.value)
    writer.write(self.close_token.value)

class TemplateType(Type):
  def __init__(self, identifier_token: Token, type_arguments: SyntaxList):
    super().__init__()
    self.identifier_token = identifier_token
    self.type_arguments = type_arguments

  def write(self, writer: TextIO):
    writer.write(self.identifier_token.value)
    self.type_arguments.write(writer)

class TupleMemberType(Type):
  def __init__(self, element_type: Type, element_name: Token):
    super().__init__()
    self.element_type = element_type
    self.element_name = element_name

  def write(self, writer: TextIO):
    self.element_type.write(writer)

class TupleType(Type):
  def __init__(self, elements: SyntaxList):
    super().__init__()
    self.elements = elements

  def write(self, writer: TextIO):
    self.elements.write(writer)

class AliasInfo(Node):
  before_set: [str]
  after_set: [str]
  contained_types: []
  tokens: [Token]

  def __init__(self):
    super().__init__()
    self.before_set = []
    self.after_set = []
    self.contained_types = []
    self.tokens = []
    self.is_writable = False

  def write(self, writer: TextIO):
    writer.write("(")
    writer.write("|".join(self.before_set))
    if self.is_writable:
      writer.write("!")
    writer.write(" -> ")
    writer.write("|".join(self.after_set))
    writer.write(")")

class AliasInfoType(Type):
  def __init__(self, inner_type: Type, alias_info: AliasInfo):
    super().__init__()
    self.inner_type = inner_type
    self.alias_info = alias_info

  def write(self, writer: TextIO):
    self.inner_type.write(writer)
    self.alias_info.write(writer)

class KWArgsSentinalType(Type):
  def __init__(self, token: Token):
    super().__init__()
    self.token = token

  def write(self, writer: TextIO):
    writer.write(self.token.value)

class TensorType(ConcreteType): pass
class IntType(ConcreteType): pass
class FloatType(ConcreteType): pass
class BoolType(ConcreteType): pass
class StrType(ConcreteType): pass
class ScalarType(ConcreteType): pass
class ScalarTypeType(ConcreteType): pass
class DimnameType(ConcreteType): pass
class GeneratorType(ConcreteType): pass
class TensorOptionsType(ConcreteType): pass
class LayoutType(ConcreteType): pass
class DeviceType(ConcreteType): pass
class MemoryFormatType(ConcreteType): pass
class QSchemeType(ConcreteType): pass
class StorageType(ConcreteType): pass
class ConstQuantizerPtrType(ConcreteType): pass
class StreamType(ConcreteType): pass

#region Decls

class Decl(Node): pass

class ParameterDecl(Decl):
  def __init__(
    self,
    parameter_type: Type,
    identifier: Token = None,
    equals: Token = None,
    default_value: Expression = None):
    super().__init__()
    self.parameter_type = parameter_type
    self.identifier = identifier
    self.equals = equals
    self.default_value = default_value

  def write(self, writer: TextIO):
    self.parameter_type.write(writer)
    if self.identifier:
      writer.write(" ")
      writer.write(self.identifier.value)

class FunctionDecl(Decl):
  def __init__(
    self,
    identifier: Token,
    parameters: SyntaxList,
    return_type: Type = None,
    semicolon: Token = None,
    arrow: Token = None):
    super().__init__()
    self.is_leaf = False
    self.identifier = identifier
    self.return_type = return_type
    self.parameters = parameters
    self.semicolon = semicolon
    self.arrow = arrow

class TranslationUnitDecl(Decl):
  def __init__(self, decls: [FunctionDecl]):
    super().__init__()
    self.decls = decls

  def __iter__(self):
    return self.decls.__iter__()

#endregion