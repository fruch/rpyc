import sys
from nose import SkipTest
if sys.version_info < (3, 0):
    raise SkipTest("Those are only for Python3")
            
from rpyc.core.vinegar_3 import dump, load, install_rpyc_excepthook, uninstall_rpyc_excepthook, rpyc_excepthook, GenericException

import traceback
from nose.tools import raises

from globals import EXCEPTION_STOP_ITERATION

#====================================================================
# Custom exceptions
#====================================================================

class my_exception_no_args(Exception):
    def __init__(self):
        self.args = ()
    def __str__(self):
        return "str: my_exception_no_args"
    def __repr__(self):
        return "repr: my_exception_no_args"

class my_exception_with_args(Exception):
    def __init__(self, err_string, err_type):
        self.args = (err_string, err_type)
        self.err_string = err_string
        self.type = err_type
    def __str__(self):
        return self.err_string
    def __repr__(self):
        return self.err_string

class remote_exception(Exception):
    def __init__(self):
        self.args = ()
    def __str__(self):
        return "str: remote computer rebelling"
    def __repr__(self):
        return "repr: remote computer rebelling"

#====================================================================
# Generic useful functions
#====================================================================

def simulate_raise_exception(my_exception):
    exception_class = type(my_exception)
    try:
        raise my_exception
    except exception_class:
        traceback_txt = traceback.format_exception(exception_class, my_exception, my_exception.__traceback__)
    return exception_class, my_exception, my_exception.__traceback__

#====================================================================
# Test vinegar module setup
#====================================================================

def test_install_and_un_hook():
    orginal_hook = sys.excepthook
    install_rpyc_excepthook()
    new_hook = sys.excepthook
    
    print("orginal_hook:", orginal_hook)
    print("new_hook:", new_hook)
    
    assert new_hook != orginal_hook
    assert new_hook == rpyc_excepthook
    
    uninstall_rpyc_excepthook()
    
    restored_hook = sys.excepthook
    
    print("restored_hook:", restored_hook)
    
    assert restored_hook == orginal_hook

#========================================================================
# Test loading and dumping of exceptions
#========================================================================

class test_dump_load(object):
    def setup(self):
        install_rpyc_excepthook()

    def teardown(self):
        uninstall_rpyc_excepthook()

    def test_StopIteration(self):
        exception_instance = StopIteration()
        cls, instance, traceback = simulate_raise_exception(exception_instance)
        brimable_data = dump(cls, instance, traceback)
        
        print("brimable_data: == EXCEPTION_STOP_ITERATION:")
        print("{0}=={1}".format(brimable_data, EXCEPTION_STOP_ITERATION))
        
        assert brimable_data == EXCEPTION_STOP_ITERATION
        
        decoded_exception = load(brimable_data)
        
        print("decoded_exception: == StopIteration:")
        print("{0}=={1}".format(type(decoded_exception), StopIteration))
        
        assert type(decoded_exception) == StopIteration
    
    def test_TypeError(self):
        exception_instance = TypeError()
        cls, instance, traceback = simulate_raise_exception(exception_instance)
        brimable_data = dump(cls, instance, traceback)
        
        (module_name, exception_class_name), arguments, attributes, traceback_txt = brimable_data
        
        print("module_name (== \"builtins\") :: ", module_name)
        assert module_name == "builtins"
        
        print("exception_class_name (== \"TypeError\") :: ", exception_class_name)
        assert exception_class_name == "TypeError"
        
        print("arguments ( == () ) :: ", arguments)
        assert arguments == ()
        
        print("attributes :: ", attributes)
        
        print("traceback_txt (not in {None, ""}) :: ", traceback_txt)
        assert traceback_txt not in (None, "")
        
        print("brimable_data () :: ")
        print("{0}".format(brimable_data))
        
        decoded_exception = load(brimable_data)
        
        print("decoded_exception: == TypeError:")
        print("{0} == {1}".format(type(decoded_exception), TypeError))
        assert type(decoded_exception) == TypeError
        
        print("check contains remote exception")
        assert decoded_exception._remote_tb[0].startswith("Traceback")
        
    def test_custom_xecpt_no_args(self):
        exception_instance = my_exception_no_args()
        cls, instance, traceback = simulate_raise_exception(exception_instance)
        brimable_data = dump(cls, instance, traceback)
        
        print("\n")
        print(brimable_data) 
        print("\n")
        
        (module_name, exception_class_name), arguments, attributes, traceback_txt = brimable_data
        
        assert exception_class_name == "my_exception_no_args"
        assert arguments == ()
        
        decoded_exception = load(brimable_data)
        
        # This decoded exception will be an generic representation of the custom exception above
        # This is because instantiate_custom_exceptions and import_custom_exceptions are both off
        
        # Should not have arguments
        
        print(dir(decoded_exception))
        
        print("decoded_exception: == my_exception_no_args:")
        print("{0} == {1}".format(type(decoded_exception), my_exception_no_args))
        assert type(decoded_exception) == my_exception_no_args
        
    def test_custom_xecpt_with_args(self):
        arguments_to_pass = "example_string", "ERROR_TYPE_TEST"
        exception_instance = my_exception_with_args(*arguments_to_pass)
        cls, instance, traceback = simulate_raise_exception(exception_instance)
        
        #Dump
        brimable_data = dump(cls, instance, traceback)
        (module_name, exception_class_name), arguments, attributes, traceback_txt = brimable_data
        
        print(exception_class_name, " == my_exception_with_args")
        assert exception_class_name == "my_exception_with_args"
        
        print(my_exception_with_args, " == ", arguments_to_pass)
        assert arguments == arguments_to_pass
        
        #Load
        decoded_exception = load(brimable_data)
        print(decoded_exception.__repr__, exception_instance.__repr__)
        print("decoded_cls : {0} == {1} : orginal_cls".format(dir(decoded_exception.__class__.__class__.__name__), exception_instance.__class__.__class__.__name__))
        assert decoded_exception.__class__ == exception_instance.__class__
        
        print("decoded_mod_name : {0} == {1} : orginal_mod_name".format(decoded_exception.__module__, my_exception_with_args.__module__))
        assert decoded_exception.__module__ == exception_instance.__module__
        
        print("decoded_args : {0} == {1} : args_given".format(decoded_exception.args, arguments_to_pass))
        assert decoded_exception.args == arguments_to_pass
        
        print("attr1 : {0} == {1} : should be".format(decoded_exception.type, arguments_to_pass[0]))
        assert decoded_exception.type == arguments_to_pass[0]
        
        print("attr2 : {0} == {1} : should be".format(decoded_exception.err_string, arguments_to_pass[1]))
        assert decoded_exception.err_string == arguments_to_pass[1]
        
        # This decoded exception will be an generic representation of the my_exception_with_args exception above
        # This is because instantiate_custom_exceptions and import_custom_exceptions are both off
        
        print("isinstance(decoded_exception, GenericException)")
        assert isinstance(decoded_exception, GenericException)
        
    def test_many(self):
        pass
    
    def test_remote_tb(self):
        pass
    
    def test_unimportable(self):
        pass
    
    def exception_from_non_imported_module(self):
        pass