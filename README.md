# Kaleidoscope_Compiler

tldr: This is a python compiler that utilizes PLY to tokenize and parse Kaleidoscope code into an AST. It then uses llvmlite to create the IR and JIT the code. Details about the language can be found in the "The Extended-Kaleidoscope" pdfs. 

example command line where input.txt contains the Kaleidsocope Code:
python ekcc.py -emit-ast -jit -O input.txt

input.txt contains example code. input.ast.yaml is the yaml ast. 

1. ekcc.py: The main script
2. global variables are defined
3. lexerAndParser.py: Uses the PLY library to tokenize and parse the code to create an AST in the form of dictionaries and lists. 
4. analyzer.py does some error checking by recursively going through the AST.
	- In 'vdecl', the type may not be void
	- In ref 'type', the type may not be void or a reference type
	- All functions must be declared/defined before being used
	- The initialization expression for a reference variable (including function arguments) must be a variable.
	- All programs must define exactly one function named “run” which returns an integer (the program exit status) and takes no arguments.
	-Every expression should have a type (int, float, etc).  When printing the AST, the type of each expression should be part of the AST nodes for each expression.
5. IR.py recursively travels the AST and uses llvmlite to build the intermediate representation. Llvmlite is a lightweight LLVM-Python binding.
6. llvm_binder.py: actually binds, compiles, and executes the IR. It injects LLVM IR code into the IR module string for the print function. It also optimizes the compilation of the code. 