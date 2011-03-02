import netref_3 as netref
#from netref_3 import

import inspect

#===================================================================

simple_dict = {1:"A", 2:{"A":"C"}}

def test_inspect_methods_dict():
    meth_doc_list_actual = netref.inspect_methods(simple_dict).items()
    meth_doc_list_expected = [(name, inspect.getdoc(attr)) for name, attr in inspect.getmembers(simple_dict, inspect.isroutine)]
    
    print("-"*40)
    print("Checking get more than inspect gets, as I going above what is in dir")
    result = (set(meth_doc_list_actual) - set(meth_doc_list_expected))
    print("RESULT=", result, "set=", set(meth_doc_list_actual) - set(meth_doc_list_expected))
    assert result
    
    print("-"*40)
    methods_actual = {name for name, attr in netref.inspect_methods(simple_dict).items()}
    a_few_expected_dict_methods = {'popitem', 'pop', 'get', 'keys', 'update', '__iter__', 'setdefault', 'items', 'clear'}
    print("Checking I get a few dict methods expected in 3.1")
    assert methods_actual > a_few_expected_dict_methods
    
    print("-"*40)
    print("check every attr is actually an attr of simple_dict")
    assert all([hasattr(simple_dict, meth) for meth in methods_actual])
    
    print("-"*40)
    print("check every attr is actually callable")
    assert all([hasattr(getattr(simple_dict, meth), "__call__") for meth in methods_actual])
    
#===================================================================

simple_list = [1, 2, 3]

def test_inspect_methods_list():
    meth_doc_list_actual = netref.inspect_methods(simple_list).items()
    meth_doc_list_expected = [(name, inspect.getdoc(attr)) for name, attr in inspect.getmembers(simple_list, inspect.isroutine)]
    
    print("-"*40)
    print("Checking get more than inspect gets, as I going above what is in dir")
    result = (set(meth_doc_list_actual) - set(meth_doc_list_expected))
    print("RESULT=", result, "set=", set(meth_doc_list_actual) - set(meth_doc_list_expected))
    assert result
    
    print("-"*40)
    methods_actual = {name for name, attr in netref.inspect_methods(simple_list).items()}
    a_few_expected_list_methods = {'append', 'pop', 'extend', 'sort', '__iter__', 'count'}
    print("Checking I get a few list methods expected in 3.1")
    assert methods_actual > a_few_expected_list_methods
    
    print("-"*40)
    print("check every attr is actually an attr of simple_list")
    assert all([hasattr(simple_list, meth) for meth in methods_actual])
    
    print("-"*40)
    print("check every attr is actually callable")
    assert all([hasattr(getattr(simple_list, meth), "__call__") for meth in methods_actual])

#===================================================================

simple_string = "example string"

def test_inspect_methods_str():
    meth_doc_list_actual = netref.inspect_methods(simple_string).items()
    meth_doc_list_expected = [(name, inspect.getdoc(attr)) for name, attr in inspect.getmembers(simple_string, inspect.isroutine)]
    
    print("-"*40)
    print("Checking get more than inspect gets, as I going above what is in dir")
    result = (set(meth_doc_list_actual) - set(meth_doc_list_expected))
    print("RESULT=", result, "set=", set(meth_doc_list_actual) - set(meth_doc_list_expected))
    assert result
    
    print("-"*40)
    methods_actual = {name for name, attr in netref.inspect_methods(simple_string).items()}
    a_few_expected_string_methods = {'startswith', 'encode', 'format', 'isdigit', 'rfind', 'strip'}
    print("Checking I get a few string methods expected in 3.1")
    assert methods_actual > a_few_expected_string_methods
    
    print("-"*40)
    print("check every attr is actually an attr of simple_string")
    assert all([hasattr(simple_string, meth) for meth in methods_actual])
    
    print("-"*40)
    print("check every attr is actually callable")
    assert all([hasattr(getattr(simple_string, meth), "__call__") for meth in methods_actual])

#===================================================================

simple_mul_tuple = ("simple_mul_tuple", [])

def test_inspect_methods_mul_tuple():
    meth_doc_list_actual = netref.inspect_methods(simple_mul_tuple).items()
    meth_doc_list_expected = [(name, inspect.getdoc(attr)) for name, attr in inspect.getmembers(simple_mul_tuple, inspect.isroutine)]
    
    print("-"*40)
    print("Checking get more than inspect gets, as I going above what is in dir")
    result = (set(meth_doc_list_actual) - set(meth_doc_list_expected))
    print("RESULT=", result, "set=", set(meth_doc_list_actual) - set(meth_doc_list_expected))
    assert result
    
    print("-"*40)
    methods_actual = {name for name, attr in netref.inspect_methods(simple_mul_tuple).items()}
    a_few_expected_mul_tuple_methods = {'__contains__', '__hash__', '__iter__', '__le__', '__len__', 'index'}
    print("Checking I get a few string methods expected in 3.1")
    assert methods_actual > a_few_expected_mul_tuple_methods
    
    print("-"*40)
    print("check every attr is actually an attr of simple_mul_tuple")
    assert all([hasattr(simple_mul_tuple, meth) for meth in methods_actual])
    
    print("-"*40)
    print("check every attr is actually callable")
    assert all([hasattr(getattr(simple_mul_tuple, meth), "__call__") for meth in methods_actual])

#===================================================================

class simple_cls(object):
    """Simple exmaple of a class, has a method simple_meth"""
    def __init__(self):
        """simple __init__"""
        self.eg_attr = "example"
    def simple_meth(self):
        """simple method doc"""
        return True

def test_inspect_methods_simple_cls():
    meth_doc_dict = netref.inspect_methods(simple_cls)
    print("-"*40)
    print("checking presence of simple method")
    assert simple_cls.simple_meth.__name__ in meth_doc_dict
    
    print("checking non presence of non callable eg_attr")
    assert "eg_attr" not in meth_doc_dict
    
    print("-"*40)
    print("checking presence of simple method doc")
    assert meth_doc_dict["simple_meth"] == simple_cls.simple_meth.__doc__

#===================================================================

simple_instance = simple_cls()

def test_inspect_methods_simple_instance():
    meth_doc_dict = netref.inspect_methods(simple_instance)
    print("-"*40)
    print("checking presence of simple method")
    assert simple_instance.simple_meth.__name__ in meth_doc_dict
    
    print("checking non presence of non callable eg_attr")
    assert "eg_attr" not in meth_doc_dict
    
    print("-"*40)
    print("checking presence of simple method doc")
    assert meth_doc_dict["simple_meth"] == simple_instance.simple_meth.__doc__

#===================================================================

def simple_function(x):
    def nested_func():
        pass
    return 4

def test_inspect_methods_simple_function():
    meth_doc_dict = netref.inspect_methods(simple_function)
    print("-"*40)
    print("checking presence of __call__ in simple function")
    print(meth_doc_dict.keys())
    assert '__call__' in meth_doc_dict
    
    print("-"*40)
    assert meth_doc_dict['__call__'] == simple_function.__call__.__doc__

#===================================================================

def test_inspect_methods_module():
    meth_doc_dict = netref.inspect_methods(inspect)
    print("-"*40)
    print("checking presence of __str__ in simple function")
    assert "__str__" in meth_doc_dict

#===================================================================

class advanced_class(simple_cls):
    def __init__(self):
        """advanced __init__"""
        pass
    def another_meth(self):
        pass

def test_inspect_methods_advanced_cls():
    meth_doc_dict = netref.inspect_methods(advanced_class)
    print("-"*40)
    print("checking presence of simple method")
    assert advanced_class.simple_meth.__name__ in meth_doc_dict
    
    print("-"*40)
    print("checking presence of simple method")
    assert advanced_class.another_meth.__name__ in meth_doc_dict
    
    print("-"*40)
    print("checking presence of correct doc method for method in both simple and advanced class")
    assert meth_doc_dict["__init__"] == advanced_class.__init__.__doc__ != simple_cls.__init__.__doc__


#===================================================================

advanced_instance = advanced_class()

def test_inspect_methods_advanced_instance():
    meth_doc_dict = netref.inspect_methods(advanced_instance)
    print("-"*40)
    print("checking presence of simple method")
    assert advanced_instance.simple_meth.__name__ in meth_doc_dict
    
    print("-"*40)
    print("checking presence of simple method")
    assert advanced_instance.another_meth.__name__ in meth_doc_dict
    
    print("-"*40)
    print("checking presence of correct doc method for method in both simple and advanced class")
    assert meth_doc_dict["__init__"] == advanced_instance.__init__.__doc__ != simple_cls.__init__.__doc__

#===================================================================

#def test_inspect_methods_metaclass():
#    assert False   # I smeta class inheratnace the correct way around, is the method doc correct

#===================================================================

#Abstract, metaclass
#mutli inheratance
#Non mro object

#It sets class in class_factory, if this uses builtin_classes_cache does it work across computers???
