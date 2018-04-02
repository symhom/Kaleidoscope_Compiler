import llvmlite.binding as llvm
from ctypes import CFUNCTYPE, c_int, c_float

def inject_built_in(module):
    built_in = 'define void @"printFloat"(float) #0 {  %2 = alloca float, align 4  store float %0, float* %2, align 4  %3 = load float, float* %2, align 4  %4 = fpext float %3 to double  %5 = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.str, i32 0, i32 0), double %4)  ret void}define void @"printInt"(i32) #0 {  %2 = alloca i32, align 4  store i32 %0, i32* %2, align 4  %3 = load i32, i32* %2, align 4  %4 = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.str.1, i32 0, i32 0), i32 %3)  ret void}define void @"printString"(i8*) #0 {  %2 = alloca i8*, align 8  store i8* %0, i8** %2, align 8  %3 = load i8*, i8** %2, align 8  %4 = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.str.2, i32 0, i32 0), i8* %3)  ret void}'
    string_declare = '''@.str = private unnamed_addr constant [4 x i8] c"%f\\0A\\00", align 1@.str.1 = private unnamed_addr constant [4 x i8] c"%d\\0A\\00", align 1@.str.2 = private unnamed_addr constant [4 x i8] c"%s\\0A\\00", align 1'''
    strings = break_run(str(module))
    return string_declare + strings[0] + built_in + strings[1]


def break_run(module_string):
    module_string = module_string.replace('declare void @"printFloat"(float %".1")', "")
    module_string = module_string.replace('declare void @"printInt"(i32 %".1")', "")
    module_string = module_string.replace('declare void @"printString"(i8* %".1")', "")

    index = module_string.index('define i32 @"run"()')
    results = [module_string[0:index], module_string[index:]]
    return results


def bind(module, *args, optimize = False):
    module = inject_built_in(module)

    llvm_ir_parsed = llvm.parse_assembly(str(module))
    if False:
        #general way of optimizing
        # print("from optimize")
        pmb = llvm.create_pass_manager_builder()
        pmb.opt_level = 3

        fpm = llvm.create_function_pass_manager(llvm_ir_parsed)
        pmb.populate(fpm)

        pm = llvm.create_module_pass_manager()
        pmb.populate(pm)
        a = pm.run(llvm_ir_parsed)
        # print(f'something was optimized {a}')


    ####################################################################
    if optimize:
        #more specific way of optimizing 
        opt_manager = llvm.PassManagerBuilder()
        mod_manager = llvm.ModulePassManager()

        mod_manager.add_constant_merge_pass()
        mod_manager.add_dead_arg_elimination_pass()
        mod_manager.add_function_inlining_pass(225)
        mod_manager.add_global_dce_pass()
        mod_manager.add_global_optimizer_pass()
        mod_manager.add_ipsccp_pass()
        mod_manager.add_dead_code_elimination_pass()
        mod_manager.add_cfg_simplification_pass()   
        mod_manager.add_gvn_pass()
        mod_manager.add_instruction_combining_pass()
        mod_manager.add_licm_pass()
        mod_manager.add_sccp_pass()
        mod_manager.add_type_based_alias_analysis_pass()
        mod_manager.add_basic_alias_analysis_pass()

        mod_manager.run(llvm_ir_parsed)

    ####################################################################

    llvm_ir_parsed.verify()


    # JIT
    target_machine = llvm.Target.from_default_triple().create_target_machine()
    engine = llvm.create_mcjit_compiler(llvm_ir_parsed, target_machine)
    engine.finalize_object()

    entry = engine.get_function_address("run")

    # arg_types = []
    # for arg in args:
    #     if type(arg) == int:
    #         arg_types.append(c_int)
    #     elif type(arg) == float:
    #         arg_types.append(c_float)
    #
    cfunc = CFUNCTYPE(c_int)(entry)
    # if len(arg_types) != 0:
    #     cfunc = CFUNCTYPE(*arg_types)(entry)

    # arg_values = []
    # for arg in args:
    #     if type(arg) == int:
    #         arg_values.append(arg)
    #     elif type(arg) == float:
    #         arg_values.append(c_float(arg))

    # result = cfunc(*arg_values)
    result = cfunc()
    print()
    print("program returns: {}".format(result))
    return llvm_ir_parsed
