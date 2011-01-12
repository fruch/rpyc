#!/usr/bin python
import types

class describer(object):
    def __init__(self, func):
        self.func = func
        self.name = self.func.__name__
    
    def __get__(self, instance, owner):
        """This: 1) determines the instance calling this wrapped function,
            2) __get__ method making this a descriptor"""
        self._instance = instance
        return types.MethodType(self, instance, owner)
    
    def __call__(self, *args, **kwargs):
        print "Called {func}, with args={the_args} and kwargs={the_kwargs}".format(func=self.name, the_args=args, the_kwargs=kwargs)
        return_arg = self.func(*args, **kwargs)
        print "returning {ret} from {func}".format(ret=return_arg, func=self.name)
        return return_arg 
    
if __name__ == "__main__":
    @describer
    def moo(x,y):
        return x+y
    
    class moo2(object):
        def __init__(self):
            pass
        def __repr__(self):
            return "moo2_instance"
        @describer
        def erm(self, x, y):
            return x+y
    
    
    moo(1,y=2)
    A=moo2()
    A.erm(1,3)