from llvmlite import ir
import llvmlite
import llvmlite.binding as llvm
from ctypes import CFUNCTYPE, c_int, c_float



llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

#####################
# The script generates the IR, executes the following code using llvmlite, and returns the value 5:

# def int main()
# 	array = [3,5,8];
# 	return array[1];
	
###################################### 
# generate the IR code 
i32 = ir.IntType(32)
f32 = ir.FloatType()

#make a module
module = ir.Module(name = "array_example")

# define function parameters for function "main"
return_type = i32 #return void
argument_types = list() #can add ir.IntType(#), ir.FloatType() for arguments
func_name = "main"

#make a function
fnty = ir.FunctionType(return_type, argument_types)
main_func = ir.Function(module, fnty, name=func_name)

# append basic block named 'entry', and make builder
# blocks generally have 1 entry and exit point, with no branches within the block
block = main_func.append_basic_block('entry')
builder = ir.IRBuilder(block)

# define array with length of 3 and type of i32
# arrays can't have different types within it
array_example = [3,5,8]
array_type = ir.ArrayType(i32, len(array_example)) #According to documentation, the second argument has to be an Python Integer. It can't be ir.Constant(i32, 3) for example.
arr = ir.Constant(array_type, array_example)
ptr = builder.alloca(array_type) #allocate memory
builder.store(arr, ptr)

#to obtain these values. Let's say we want to get index 1
int_0 = ir.Constant(i32, 0)
index1 = ir.Constant(i32, 1)

#allocate for the number 1
ptr_arg = builder.alloca(i32)
builder.store(index1, ptr_arg)
value = builder.load(ptr_arg)

#the address of array[index] that we want
address = builder.gep(ptr, [int_0,value]) #you need int_0
# I would avoid using IRbuilder.extract_value(agg, index), because the index has to be a Python integer, 
# and not a loaded value from the IR representation unlike IRbuider.gep. For example...

# variable = a *b+ 1
# array = [1,2,3]
# array[variable]  can't use extract_value because you don't know what value 'variable' 
# is until run time, and extract_value uses python integer
# array[0]  can use extract_value, because you know at compile time that the index is '0' and can use the python integer '0'


# we return this value
builder.ret(builder.load(address))
#End of IR generation
############################
#Excute the generated IR without any optimizations. Nothing special is required. 
llvm_ir_parsed = llvm.parse_assembly(str(module))
llvm_ir_parsed.verify()

# JIT
target_machine = llvm.Target.from_default_triple().create_target_machine()
engine = llvm.create_mcjit_compiler(llvm_ir_parsed, target_machine)
engine.finalize_object()

#Run the function with name func_name. This is why it makes sense to have a 'main' function that calls other functions.
entry = engine.get_function_address(func_name) 
cfunc = CFUNCTYPE(c_int)(entry)
result = cfunc()

print('The llvm IR generated is:')
print(module)
print()
print(f'It returns {result}')

#the result printed out is

# The llvm IR generated is:
# ; ModuleID = "array_example"
# target triple = "unknown-unknown-unknown"
# target datalayout = ""

# define i32 @"main"() 
# {
# entry:
#   %".2" = alloca [3 x i32]
#   store [3 x i32] [i32 3, i32 5, i32 8], [3 x i32]* %".2"
#   %".4" = alloca i32
#   store i32 1, i32* %".4"
#   %".6" = load i32, i32* %".4"
#   %".7" = getelementptr [3 x i32], [3 x i32]* %".2", i32 0, i32 %".6"
#   %".8" = load i32, i32* %".7"
#   ret i32 %".8"
# }



# It returns 5
