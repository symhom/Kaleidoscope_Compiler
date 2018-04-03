from llvmlite import ir
import llvmlite
import llvmlite.binding as llvm
from ctypes import CFUNCTYPE, c_int, c_float



llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

#####################
# The script generates the IR, executes the following code using llvmlite, and returns the value 48:

# def int main()
#	int x = 3;
#	int i = 1;

#	while (i < 5){
#	x = x * 2;
# 	i = i + 1;
#	}

#	return x; 

# generate the IR code
###################################### 
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


########################################
# symbol table generation, key = variable name, value = pointer 

x_value = ir.Constant(i32, 3) #create the values
i_value = ir.Constant(i32, 1)
x_pointer = builder.alloca(i32) #create the addresses
i_pointer = builder.alloca(i32)
builder.store(x_value, x_pointer) #store those values at those addresses
builder.store(i_value, i_pointer)

symbol_table ={"x":x_pointer, "i":i_pointer}

##########################################
# while loop. 

w_body_block = builder.append_basic_block("w_body")
w_after_block = builder.append_basic_block("w_after")

# head 
# initial checking of while (i < 5)
constant_5 = ir.Constant(i32, 5)
current_i_value = builder.load(symbol_table["i"]) #loads the value of i_pointer
cond_head = builder.icmp_signed('<', current_i_value, constant_5, name="lt") #returns boolean, which is ir.IntType(1)

#for the first checking of (i<5), it could go straight from the the head to w_after_block
# if i is already greater than 5. It needs to check whether to start the loop at all. 
builder.cbranch(cond_head, w_body_block, w_after_block)

# body
builder.position_at_start(w_body_block)
current_x_value = builder.load(symbol_table["x"])
current_i_value = builder.load(symbol_table["i"])

# x = x * 2
# i = i + 1
new_x_value = builder.mul(current_x_value, ir.Constant(i32, 2), name='mul')
new_i_value = builder.add(current_i_value, ir.Constant(i32,1), name="add")
builder.store(new_x_value, symbol_table["x"]) #store the new x value at the x pointer
builder.store(new_i_value, symbol_table["i"])

#at the end of the w_body_block, you need to check i < 5 again, because there's a branch possibility
# if true, it returns to the top of the w_body_block. If false, it exits the loop
cond_body = builder.icmp_signed('<', new_i_value, constant_5, name="lt")
builder.cbranch(cond_body, w_body_block, w_after_block)
# after
builder.position_at_start(w_after_block)

##############################
# return x
x_address = symbol_table["x"]
x_value = builder.load(x_address)
# we return this value

builder.ret(x_value)

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
#   %".2" = alloca i32
#   %".3" = alloca i32
#   store i32 3, i32* %".2"
#   store i32 1, i32* %".3"
#   %".6" = load i32, i32* %".3"
#   %"lt" = icmp slt i32 %".6", 5
#   br i1 %"lt", label %"w_body", label %"w_after"
# w_body:
#   %".8" = load i32, i32* %".2"
#   %".9" = load i32, i32* %".3"
#   %"mul" = mul i32 %".8", 2
#   %"add" = add i32 %".9", 1
#   store i32 %"mul", i32* %".2"
#   store i32 %"add", i32* %".3"
#   %"lt.1" = icmp slt i32 %"add", 5
#   br i1 %"lt.1", label %"w_body", label %"w_after"
# w_after:
#   %".13" = load i32, i32* %".2"
#   ret i32 %".13"
# }


# It returns 48