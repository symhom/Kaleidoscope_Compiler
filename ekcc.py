from yaml import dump
import argparse
import mmap
import sys
import lexerAndParser
import analyzer
import IR
import llvm_binder

def readFile(fileName):
  f = open(fileName,"r")
  mMap = mmap.mmap(f.fileno(),0, prot = mmap.PROT_READ)
  stringFile =str(mMap[:])
  stringFile = stringFile[2:-1]
  data = mMap[:].decode('ascii')
  return data

def emitAst(fileName, output):
  yaml = dump(output, default_flow_style=False)
  file = open(fileName, 'w')
  file.write(yaml)
  file.close()


def emit_ir(fileName, module):
  file = open(fileName, 'w')
  file.write(
      str(module)
  )
  file.close()


if __name__== "__main__":
  parser = argparse.ArgumentParser(
    description='Sarah and Hao\' Compiler')
  parser.add_argument('input_file', metavar='input_file',
                    help='input file name')
  parser.add_argument('-emit-ast', action='store_true',
                    default=False,
                    dest='boolean_emit_ast',
                    help='generate ast'),
  parser.add_argument('-emit-llvm', action='store_true',
                  default=False,
                  dest='boolean_emit_llvm',
                  help='generate ast')
  parser.add_argument('-jit', action='store_true',
                default=False,
                dest='boolean_jit',
                help='generate ast'),
  parser.add_argument('-o', action='store',
                    dest='output_file',
                    help='output file name',
                    required=False)
  parser.add_argument('-O3)', action='store_true',
                  dest='optimization3',
                  help='optimization IR',
                  required=False)
  parser.add_argument('sysarg', nargs='*')
  args = parser.parse_args()
  if not args.boolean_jit and args.output_file is None:
      raise RuntimeError("at least one of -jit or -o should be specified!")

  code = readFile(args.input_file)
  ast = lexerAndParser.toAst(code)
  if ast is None:
      raise RuntimeError('AST parsing failure')
  errors = analyzer.semanticsCheck(ast)

  if args.boolean_emit_ast:
    emitAst(args.input_file.rsplit('.', 1)[0] + '.ast.yaml', ast)

  module = IR.mainFunc(ast, args.sysarg)


  if args.boolean_jit:
      module = llvm_binder.bind(module, args.sysarg, optimize = args.optimization3)
      # module = str(module)

  if args.boolean_emit_llvm:
    emit_ir(args.output_file.rsplit('.', 1)[0] + '.ll', module)

  exitCode = len(errors)
  print('exit: ' + str(exitCode))
  sys.exit(exitCode)

