import netref_3 as netref
#from netref_3 import

simple_dict = {1:"A", 2:"B"}

class simple_cls(object):
    """Simple exmaple of a class, has a method simple_meth"""
    def __init__(self):
        """simple cls init doc"""
        pass
    def simple_meth(self):
        """simple method doc"""
        return True

def test_inspect_methods_dict():
    meth_doc_list = netref.inspect_methods(simple_dict)
    print(meth_doc_list)
    assert False

def test_inspect_methods_list():
    assert False

def test_inspect_methods_str():
    assert False

def test_inspect_methods_int():
    assert False

def test_inspect_methods_simple_cls():
    meth_doc_list = netref.inspect_methods(simple_cls)
    meth_doc_dict = dict(meth_doc_list)
    print("-"*40)
    print("checking presence of simple method")
    assert simple_cls.simple_meth.__name__ in meth_doc_dict
    
    print("-"*40)
    print("checking presence of simple method doc")
    assert meth_doc_dict["simple_meth"] == simple_cls.simple_meth.__doc__

def test_inspect_methods_simple_instance():
    assert False

def test_inspect_methods_advanced_cls():
    assert False

def test_inspect_methods_advanced_instance():
    assert False

#Abstract, metaclass
#mutli inheratance
#Non mro object

#It sets class in class_factory, if this uses builtin_classes_cache does it work across computers???
