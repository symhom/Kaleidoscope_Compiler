# Kaleidoscope_Compiler

tldr: This is a python compiler that utilizes PLY to tokenize and parse Kaleidoscope code into an abstract syntax tree (AST). It then uses llvmlite to create the IR and JIT the code. Details about the language can be found in the "The Extended-Kaleidoscope" pdfs. 

example command line where input.txt contains the Kaleidsocope Code:
python ekcc.py -emit-ast -jit -O input.txt

input.txt contains example code. input.ast.yaml is the yaml ast of the example code. 

## Python code
1. ekcc.py: The main script
2. constants.py: global variables are defined
3. lexerAndParser.py: Uses the PLY library to tokenize and parse the code to create an AST in the form of dictionaries and lists. http://www.dabeaz.com/ply/ply.html
4. analyzer.py does some error checking by recursively going through the AST.
	- In 'vdecl', the type may not be void
	- In ref 'type', the type may not be void or a reference type
	- All functions must be declared/defined before being used
	- The initialization expression for a reference variable (including function arguments) must be a variable.
	- All programs must define exactly one function named “run” which returns an integer (the program exit status) and takes no arguments.
	- Every expression should have a type (int, float, etc).  When printing the AST, the type of each expression should be part of the AST nodes for each expression.
5. IR.py recursively travels the AST and uses llvmlite to build the intermediate representation. Llvmlite is a lightweight LLVM-Python binding. https://llvmlite.readthedocs.io/en/latest/index.html
6. llvm_binder.py: actually binds, compiles, and executes the IR. It injects LLVM IR code into the IR module string for the print function. It also optimizes the compilation of the code. 

## short__llvmlite_examples
The folder contains short self-contained examples/tutorials of llvmlite code. It does not generate the IR by recurisvely going through the AST, but instead builds it up manually line by line. It includes llvmlite examples of creating arrays, 'for' loops, and 'while' loops. 

#### array_example.py
It goes over a simple example where it creates an array and accesses a value from it. Creates the IR representation of the below code. 

```
def int main()
    array = [3,5,8];
    return array[1];
```

#### array_example_with_variables.py
It goes over a slightly different way to make arrays, especially when the array values are only known at run time. Creates the IR representation of the below code. 
```
def int main()
    int x = 3;
    int y = x * 2 -1;
    array = [x,y,8];
    return array[1];
```

#### for_loop_example.py
Llvmlite example of creating the llvm IR of a 'while' loop. Very similar to a 'while' loop. It also uses a symbol table to keep track of the 'i' values and array. Creates the IR representation of the below code.

```
def int_array_length_3 main()
    array = [3,5,8]

    for (int i = 0; i < 3; i++)
    {
        array[i] = array[i] + 1
    }
    return array; 
``` 

#### while_loop_example.py
Llvmlite example of creating the llvm IR of a 'while' loop. Creates the IR representation of the below code. 
```
def int main()
    int x = 3;
    int i = 1;

    while (i < 5){
    x = x * 2;
    i = i + 1;
    }

    return x; 

```
