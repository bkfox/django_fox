# FIXME: optimize -> set property as value, add __prop_method on value

__all__ = ('cached_result', 'cached_method', 'class_property', 'bind_property')


def cached_result(func):
    """
    Cache result of function call (that does not take calling arguments).

    Add extra `reset()` method to clear cache.
    """
    def decorator():
        if not hasattr(decorator, 'result'):
            setattr(decorator, 'result', func())
        return getattr(decorator, 'result')
    decorator.reset = lambda: delattr(decorator, 'result')
    return decorator


def cached_method(func):
    """
    Cache result of a method, including at class level. It assumes that
    input parameters wont change (look at `functools.lru_cache` for
    such usage).
    """
    key = '__cache_' + func.__name__
    def decorator(cl, *args, _cache_reset=False, **kwargs):
        # use on dict level: avoid clash on class inheritance
        if _cache_reset or (key not in cl.__dict__):
            v = func(cl, *args, **kwargs)
            setattr(cl, key, v)
            decorator.reset = lambda value=None: delattr(cl, key)
        return getattr(cl, key)

    return decorator


# Class property: original code by Mahmoud Abdelkader's answer found on
# StackOverflow #5189699
class ClassProperty:
    """
    Property descriptor used to have class properties.
    """
    def __init__(self, fget, fset=None):
        self.fget = fget
        self.fset = fset

    def __get__(self, obj, cl=None):
        if cl is None:
            cl = type(obj)
        return self.fget.__get__(obj, cl)()

    def __set__(self, obj, value):
        if not self.fset:
            raise AttributeError("can't set attribute")
        type_ = type(obj)
        return self.fset.__get__(obj, type_)(value)

    def setter(self, func):
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
        self.fset = func
        return self


def class_property(func):
    """
    Transform class/static method into a class property. It can be
    combined with `cache_method` in order to cache results
    """
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)
    return ClassProperty(func)


def bind_property(obj_attr, value_attr, default=None, is_dict=False):
    """
    Creates a property bound to an object's attribute owned by an
    instance.

    :param str obj_attr: object attribute name
    :param str value_attr: attribute on object to return
    :param object default: default value if not found
    :param bool is_dict: if True, obj is considered as a dict

    Example::

        class MyComponent:
            a = 13
            b = 12

        class MyClass:
            component = MyComponent()

            # bind value to component.a
            a = bind_property('component', 'a')

        my_class = MyClass()
        print(my_class.a)

    """
    if is_dict:
        def getter(self):
            obj = getattr(self, obj_attr)
            return obj.get(value_attr, default)
    else:
        def getter(self):
            obj = getattr(self, obj_attr)
            return getattr(obj, value_attr, default)
    return property(getter)



