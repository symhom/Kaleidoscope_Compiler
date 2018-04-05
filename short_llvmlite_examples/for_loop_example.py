from llvmlite import ir
import llvmlite
import llvmlite.binding as llvm
from ctypes import CFUNCTYPE, c_int, c_float



llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

#####################
# The script generates the IR, executes the following code using llvmlite, and returns [4,6,9]

# def int_array_length_3 main()
# 	array = [3,5,8]

# 	for (int i = 0; i < 3; i++)
# 	{
# 		array[i] = array[i] + 1
# 	}
# 	return array; 


# generate the IR code
###################################### 
# the initial part: define module, function, basic block, etc

i32 = ir.IntType(32) #integer with 32 bits
i32_0 = ir.Constant(i32,0)
i32_1 = ir.Constant(i32,1)
i32_3 = ir.Constant(i32,3)

#make a module
module = ir.Module(name = "array_example")

# define function parameters for function "main"
return_type = ir.ArrayType(i32, 3) #the return type is an array with 3 32-bit integers

argument_types = list() #can add ir.IntType(#), ir.FloatType() for arguments
func_name = "main"

#make a function
fnty = ir.FunctionType(return_type, argument_types)
main_func = ir.Function(module, fnty, name=func_name)

# append basic block named 'entry', and make builder
# blocks generally have 1 entry and exit point, with no branches within the block
block = main_func.append_basic_block('entry')
builder = ir.IRBuilder(block)


########################################
#array = [3,5,8]
array_example = [3,5,8]
array_type = ir.ArrayType(i32, 3) #According to documentation, the second argument has to be an Python Integer. It can't be ir.Constant(i32, 3) for example.
arr = ir.Constant(array_type, array_example)
ptr = builder.alloca(array_type) #allocate memory
builder.store(arr, ptr)

#add variable 'array' to the symbol table
symbol_table = {"array":ptr}

#
for_body_block = builder.append_basic_block("for_body")
for_after_block = builder.append_basic_block("for_after")

#initiailize i = 0
#for (int i = 0;...) part
i_ptr = builder.alloca(i32)
i_value = i32_0
builder.store(i_value, i_ptr) #store the value 0 to the address allocated
symbol_table["i"] = i_ptr

#does the initial i <3; Since i = 0, this is trivial

current_i_value = builder.load(symbol_table["i"])
cond_head = builder.icmp_signed('<', current_i_value, i32_3, name="lt") #returns boolean, which is ir.IntType(1)

#branches depending on whether cond_head is true or false
builder.cbranch(cond_head, for_body_block, for_after_block)
builder.position_at_start(for_body_block)

#array[i] = array[i] + 1
current_i_value = builder.load(symbol_table["i"]) #gets value of i (0,1 or 2)
array_i_pointer = builder.gep(symbol_table["array"], [i32_0,current_i_value]) #accesses array[i]
array_i_value = builder.load(array_i_pointer)
new_array_i_value = builder.add(array_i_value, i32_1, name="add") #array[i] + 1
builder.store(new_array_i_value, array_i_pointer) #store the new value of array[i]


#i++
new_i_value = builder.add(current_i_value, i32_1, name="add")
builder.store(new_i_value, symbol_table["i"]) #store the new value of i at the i pointer

#compare i < 3
cond_body = builder.icmp_signed('<', new_i_value, i32_3, name="lt")
builder.cbranch(cond_body, for_body_block, for_after_block) #iterate again if true, leave if false

# after
builder.position_at_start(for_after_block)
##############################################
#after for loop 
#return array
# array = builder.load(symbol_table["array"])
# builder.ret(array)


# return x
address = symbol_table["array"]
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


# The llvm IR generated is:
# ; ModuleID = "array_example"
# target triple = "unknown-unknown-unknown"
# target datalayout = ""

# define [3 x i32] @"main"() 
# {
# entry:
#   %".2" = alloca [3 x i32]
#   store [3 x i32] [i32 3, i32 5, i32 8], [3 x i32]* %".2"
#   %".4" = alloca i32
#   store i32 0, i32* %".4"
#   %".6" = load i32, i32* %".4"
#   %"lt" = icmp slt i32 %".6", 3
#   br i1 %"lt", label %"for_body", label %"for_after"
# for_body:
#   %".8" = load i32, i32* %".4"
#   %".9" = getelementptr [3 x i32], [3 x i32]* %".2", i32 0, i32 %".8"
#   %".10" = load i32, i32* %".9"
#   %"add" = add i32 %".10", 1
#   store i32 %"add", i32* %".9"
#   %"add.1" = add i32 %".8", 1
#   store i32 %"add.1", i32* %".4"
#   %"lt.1" = icmp slt i32 %"add.1", 3
#   br i1 %"lt.1", label %"for_body", label %"for_after"
# for_after:
#   %".14" = load [3 x i32], [3 x i32]* %".2"
#   ret [3 x i32] %".14"
# }
