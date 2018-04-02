import ply.lex as lex
import ply.yacc as yacc
import sys
from constants import *


names ={}
RESERVED = {
  'if' : 'If',
  'return' : 'Return',
  'while' : 'While',
  'else' : 'Else',
  'print' : 'Print',
  'def' : 'DEF',
  'int' : 'int',
  'cint' : 'cint',
  'float' : 'float',
  'sfloat' : 'sfloat',
  'void' : 'void',
  'ref' : 'ref',
  'noalias' : 'noalias',
  'extern' : 'EXTERN'
}

tokens = [
   'lit',
   'slit',

   'PLUS',
   'Minus',
   'Multiply',
   'Divide',
   'Equal',

   'Equality',
   'lessThan',
   'greaterThan',
   'logicalOr',
   'logicalAnd',
   'logicalNegation',

   'LParen',
   'RParen',
   'LBracket',
   'RBracket',
   'COMMA',

   'newline',
   'var',
   'GLOBID',
   'Comment',
   'Semicolon'
] + list(RESERVED.values())


# Regular expression rules for simple tokens
t_PLUS    = r"\+"
t_Minus   = r'-'
t_Multiply   = r'\*'
t_Divide  = r'/'

t_Equality = r'=='
t_Equal = r'='

t_lessThan = r'<'
t_greaterThan = r'>'
t_logicalOr = r'\|\|'
t_logicalNegation = r'!'
t_logicalAnd = r'&&'

t_LParen  = r'\('
t_RParen  = r'\)'
t_LBracket = r'{'
t_RBracket = r'}'
t_COMMA = r','

t_Semicolon = r';'

# t_slit = r'"[^"]*"'

def t_slit(t):
  r'"[^"]*"'
  t.value = t.value[1:-1]
  return t


############## comment ##############
def t_Comment(t):
  r'\#.*'
  # print(t.value + 'ignored')
  pass

############## var ##############
def t_var(t):
  r'[$][\s]*[a-zA-Z_][a-zA-Z0-9_]*'
  t.value = t.value[1:].strip()
  return t

############## lit ##############
# Check for reserved words
def t_lit(t):
  r'[0-9]+(\.[0-9]+)?'
  t.value = t.value.replace(" ", "")
  if '.' in t.value:
    t.value = float(t.value)
  else:
    t.value = int(t.value)
  t.type = 'lit'
  return t

############## globid ##############
def t_GLOBID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = RESERVED.get(t.value, "GLOBID")
    return t
    #code for t_ID gotten from http://www.dabeaz.com/ply/ply.html#ply_nn3


# Define a rule so we can track line numbers
def t_newline(t):
  r'\n+'
  t.lexer.lineno += len(t.value)
  pass

#code from t_ignore to while loop is from dabeaz
t_ignore  = ' \t'
# r'[ \t]+

# Error handling rule
def t_error(t):
    print('Illegal character: ' + t.value[0])
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()


#################################################
#                  parsing                      #
#################################################

############### prog ##############
def p_prog(p):
  '''prog : funcs
          | externs funcs'''
  if len(p) == 2:
    p[0] = {name: prog, funcs: p[1]}
  else:
    p[0] = {name: prog, funcs: p[2], externs: p[1]}

def p_externs(p):
  '''externs : extern
             | extern externs'''
  if len(p) == 2:
    p[0] = {name: externs, externs:[p[1]]}
  else:
    appendByKey(p[2], externs, p[1])
    p[0] = p[2]

def p_funcs(p):
  '''funcs : func
           | func funcs'''
  if len(p) == 2:
    p[0] = {name: funcs, funcs:[p[1]]}
  else:
    appendByKey(p[2], funcs, p[1])
    p[0] = p[2]

############### extern ##############
def p_extern(p):
  '''extern : EXTERN TYPE GLOBID LParen RParen Semicolon'''
  p[0] = {name: extern, ret_type: p[2], globid:p[3]}

def p_externWithTypes(p):
  '''extern : EXTERN TYPE GLOBID LParen tdecls RParen Semicolon'''
  p[0] = {name: extern, ret_type: p[2], globid:p[3], tdecls: p[5]}

# ############## func ##############
def p_func(p):
  '''func : DEF TYPE GLOBID LParen RParen blk'''
  p[0] = {name: func, ret_type: p[2], globid: p[3], blk: p[6]}

def p_funcWithParams(p):
  '''func : DEF TYPE GLOBID LParen vdecls RParen blk'''
  p[0] = {name: func, ret_type: p[2], globid: p[3], vdecls: p[5], blk:p[7]}

# ############## blk ##############
def p_blk(p):
  '''blk : LBracket stmts RBracket'''
  p[0] = {name: blk, contents: p[2]}

def p_blkEmpty(p):
  '''blk : LBracket RBracket'''
  p[0] = {name: blk}

# ############# stmts ##############
def p_statements(p):
  '''stmts : stmt
           | stmt stmts'''
  if len(p) == 2:
    p[0] = {name: stmts, stmts: [p[1]]}
  else :
    appendByKey(p[2], stmts, p[1])
    p[0] = p[2]

# ############# stmt ##############
def p_blkStmt(p):
  '''stmt : blk'''
  p[0] = {name: blk, contents: p[1]}

def p_return(p):
  '''stmt : Return Semicolon
          | Return exp Semicolon'''
  if len(p) == 4:
    p[0] = {name: ret, exp: p[2]}
  else:
    p[0] = {name: ret}


def p_vdeclStmt(p):
  '''stmt : vdecl Equal exp Semicolon'''

  #because so far, we assume literals are either ints or floats
  #we need to account for cints and sfloats
  if "sfloat" in p[1]["type"]:
    p[3]["type"] = "sfloat"
  if "cint" in p[1]["type"]:
    p[3]["type"] = "cint"

  p[0] = {name: vardeclstmt, vdecl: p[1], exp: p[3]}

def p_expSemi(p):
  '''stmt : exp Semicolon'''
  p[0] = {name: expstmt, exp: p[1]}

def p_while(p):
   '''stmt : While LParen exp RParen stmt'''
   p[0] = {name: whileStmt, cond: p[3], stmt: p[5]}

def p_if(p):
  '''stmt : If LParen exp RParen stmt
          | If LParen exp RParen stmt Else stmt'''
  if len(p) == 6:
    p[0] = {name: ifStmt, cond: p[3], stmt: p[5]}
  else:
    p[0] = {name: ifStmt, cond: p[3], stmt: p[5], else_stmt: p[7]}

def p_print(p):
  '''stmt : Print exp Semicolon'''
  p[0] = {name : printStmt, exp : p[2]}

# ############## exps ##############
def p_exps(p):
  ''' exps : exp
           | exp COMMA exps'''
  if len(p) == 2:
    p[0] = {exps: [p[1]]}
  else:
    appendByKey(p[3], exps, p[1])
    p[0] = p[3]

def p_expParen(p):
  '''exp : LParen exp RParen'''
  p[0] = p[2]

def p_exp(p):
  '''exp : lit'''
  if '.' in str(p[1]):
    p[0] = {name: litExp, value: p[1], typ: "sfloat"}
  else:
    p[0] = {name: litExp, value: p[1], typ: "int"}

def p_slit(p):
  '''exp : slit''' 
  p[0] = {name: slitExp, value: p[1], typ: "slit"}

def p_expBinOpUop(p):
  '''exp : binop
         | uop'''
  p[0] = p[1]

def p_var(p):
  '''exp : var'''
  p[0] = {name: varExp, var: p[1]}

def p_expGlobid(p):
  '''exp : GLOBID expWrapper'''
  p[0] = {name: funcCallExp, globid: p[1], params: p[2]}

def p_expWrapper(p):
  '''expWrapper : LParen RParen
                | LParen exps RParen'''
  if len(p) == 3:
    p[0] = []
  else:
    p[0] = p[2]

############ binop ##############
def p_binop(p):
  '''binop : exp Multiply exp
           | exp PLUS exp
           | exp Divide exp
           | exp Minus exp
           | var Equal exp
           | exp Equality exp
           | exp lessThan exp
           | exp greaterThan exp
           | exp logicalAnd exp
           | exp logicalOr exp'''
  if p[2] == '*':
    p[0] = {"name": binop, "lhs": p[1], "op": 'mul', "rhs": p[3]}
  elif p[2] == '/':
    p[0] = {"name": binop, "lhs": p[1], "op": 'div', "rhs": p[3]}
  elif p[2] == '+':
    p[0] = {"name": binop, "lhs": p[1], "op": 'add', "rhs": p[3]}
  elif p[2] == '-':
    p[0] = {"name": binop, "lhs": p[1], "op": 'sub', "rhs": p[3]}
  elif p[2] == '=':
    p[0] = {"name": assign, "var": p[1], "exp": p[3]}
  elif p[2] == '==':
    p[0] = {"name": binop, "lhs": p[1], "op": 'eq', "rhs": p[3]}
  elif p[2] == '<':
    p[0] = {"name": binop, "lhs": p[1], "op": 'lt', "rhs": p[3]}
  elif p[2] == '>':
    p[0] = {"name": binop, "lhs": p[1], "op": 'gt', "rhs": p[3]}
  elif p[2] == '&&':
    p[0] = {"name": binop, "lhs": p[1], "op": 'logAnd', "rhs": p[3]}
  elif p[2] == '||':
    p[0] = {"name": binop, "lhs": p[1], "op": 'logOr', "rhs": p[3]}

############## uop ##############
def p_uop(p):
  '''uop : Minus exp %prec UOP
          | logicalNegation exp %prec UOP'''
  if p[1] == "-":
    p[0] = {"name" : uop, "uopType": "Minus", "exp": p[2] }
  else:
    p[0] = {"name" : uop, "uopType": "logicalNeg", "exp": p[2]}

############## var ##############
def p_vdecls(p):
  '''vdecls : vdecl COMMA vdecls
            | vdecl'''
  if len(p) == 4:
    appendByKey(p[3], vars_, p[1])
    p[0] = p[3]
  else:
    p[0] = {name: vdecls, vars_: [p[1]]}

def p_vdeclare(p):
  '''vdecl : TYPE var'''
  p[0] = {node: vdecl, typ: p[1], var: p[2]}


def p_tdecls(p):
  '''tdecls : TYPE
            | TYPE COMMA tdecls'''
  if len(p) == 2:
    p[0] = {name: tdecls, 'types': [p[1]]}
  else :
    appendByKey(p[3], 'types', p[1])
    p[0] = p[3]

def p_type(p):
  '''TYPE : int
          | float
          | cint
          | sfloat
          | void'''
  p[0] = p[1]

def p_refType(p):
  '''TYPE : ref TYPE'''
  p[0] = 'ref ' + p[2]


def p_refTypeNoAlias(p):
  '''TYPE : noalias ref TYPE'''

  p[0] = 'noalias ref ' + p[3]


precedence = (
  ('right', 'Equal'),
  ('left', 'logicalOr'),
  ('left', 'logicalAnd'),
  ('left', 'Equality'),
  ('left', 'lessThan', 'greaterThan'),
  ('left', 'PLUS', 'Minus'),
  ('left','Multiply','Divide'),
  ('left','UOP'),
  )

############# helper ############

def errorOut(msg):
  print(error + ": " + msg)

def appendByKey(dictonary, key, value):
  dictonary[key].insert(0,value)
  return dictonary

############# main ############
def toAst(code):
  yacc.yacc()
  ast = yacc.parse(code, debug=False)
  return ast
