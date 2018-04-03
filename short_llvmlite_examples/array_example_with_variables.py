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
#	int x = 3;
#	int y = x * 2 -1;
# 	array = [x,y,8];
# 	return array[1];
	
###################################### 
# generate the IR code 
# the initial part: define module, function, basic block, etc

i32 = ir.IntType(32) #integer with 32 bits

#make a module
module = ir.Module(name = "array_example")

# define function parameters for function "main"
return_type = i32 #return int
argument_types = list() #can add ir.IntType(#), ir.FloatType() for arguments
func_name = "main"

#make a function
fnty = ir.FunctionType(return_type, argument_types)
main_func = ir.Function(module, fnty, name=func_name)

# append basic block named 'entry', and make builder
# blocks generally have 1 entry and exit point, with no branches within the block
block = main_func.append_basic_block('entry')
builder = ir.IRBuilder(block)

###################################### 
#alternative method - allocate memory for array
array_type = ir.ArrayType(i32, 3) #3 integers of bit 32
array_pointer = builder.alloca(array_type) #pointer to array
#no values have been stored yet 

i32_0 = ir.Constant(i32, 0)
i32_1 = ir.Constant(i32, 1)
i32_2 = ir.Constant(i32, 2)


#can also just loop through to get this
pointer_to_index_0 = builder.gep(array_pointer, [i32_0, i32_0]) #gets address of array[0]
pointer_to_index_1 = builder.gep(array_pointer, [i32_0, i32_1]) #gets address of array[1]
pointer_to_index_2 = builder.gep(array_pointer, [i32_0, i32_2]) #gets address of array[2]

# then you can just store whatever value you want using the pointer directly to the array
# builder.store(value,pointer_to_index), as opposed to using builder.alloca(i32) for an individual value




#######################################
# Example using symbol table, and assigning value to certain indices 

# For the variable stuff, we don't define a variable 'x' in the IR.
# Instead, we can keep track of it in a symbol table where key = variable_name, value = IR pointer
# It is a bit overkill to use a symbol table for this code, but symbol tables can be used to maintain 
# information about scope 
symbol_table = {}
#key = variable name, value = pointer

# int x = 3
symbol_table["x"] = pointer_to_index_0 #add variable 'x' and its pointer to symbol table
x_value = ir.Constant(i32, 3) #
builder.store(x_value, pointer_to_index_0) #store the value i32 3 to array[0]

#int y, allocate memory, add it to symbol table, etc
symbol_table["y"] = pointer_to_index_1

# below does x * 2
rhs = builder.load(symbol_table["x"]) #get the pointer from the variable "x"
lhs = ir.Constant(i32, 2)
y_value = builder.mul(lhs,rhs, name = 'mul')
# subtracts 1 from x*2
rhs = y_value
lhs = ir.Constant(i32, 1)
y_value = builder.sub(rhs, lhs, name ='sub')

#store the y_value to index 1 
builder.store(y_value, pointer_to_index_1)

#allocate space for the constant 8
value_8 = ir.Constant(i32, 8)
builder.store(value_8, pointer_to_index_2)

######################################
# getting the value of a certain index, in this case, index 1

address = builder.gep(array_pointer, [i32_0,i32_1]) 
value = builder.load(address)
# we return this value

builder.ret(value)


#End of IR generation
############################
# Excute the generated IR without any optimizations. Nothing special is required in this part. 
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

# The llvm IR generated is:
# ; ModuleID = "array_example"
# target triple = "unknown-unknown-unknown"
# target datalayout = ""

# define i32 @"main"() 
# {
# entry:
#   %".2" = alloca [3 x i32]
#   %".3" = getelementptr [3 x i32], [3 x i32]* %".2", i32 0, i32 0
#   %".4" = getelementptr [3 x i32], [3 x i32]* %".2", i32 0, i32 1
#   %".5" = getelementptr [3 x i32], [3 x i32]* %".2", i32 0, i32 2
#   store i32 3, i32* %".3"
#   %".7" = load i32, i32* %".3"
#   %"mul" = mul i32 2, %".7"
#   %"sub" = sub i32 %"mul", 1
#   store i32 %"sub", i32* %".4"
#   store i32 8, i32* %".5"
#   %".10" = getelementptr [3 x i32], [3 x i32]* %".2", i32 0, i32 1
#   %".11" = load i32, i32* %".10"
#   ret i32 %".11"
# }


# It returns 5

