import copy
import functools
import inspect

from argparse import Namespace


def contracts(preconditions=(), postconditions=()):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try: __testmode__
            except: raise NameError("__testmode__ not set")


            if __testmode__:
                fails = []
                for i,func in enumerate(preconditions):
                    if not callCondition(fn, func, args, kwargs): fails.append(i)
                if fails:
                    raise PreConditionError(f"PreCondition functions failed on {fn.__name__} in {inspect.getabsfile(fn)}:{inspect.getsourcelines(fn)[1]}:\n\t {','.join(map(str, fails))}")

            if postconditions: __old__, __id__ = cacheOld(fn, args, kwargs)

            fn.__globals__['__testmode__'] = __testmode__
            try:
                __return__ = fn(*args, **kwargs)
            except Exception as e:
                print("DEBUG:", fn)
                # fn(*args)
                raise

            if __testmode__:
                fails = []
                extra = {'__return__': __return__, '__old__': __old__, '__id__': __id__} if postconditions else None
                for i,func in enumerate(postconditions):
                    func.__globals__['__old__'] = __old__
                    func.__globals__['__id__'] = __id__
                    func.__globals__['__return__'] = __return__

                    if not callCondition(fn, func, args, kwargs, extra): fails.append(i)
                if fails: raise PostConditionError("PostCondition functions failed on {} in {}:{}:\n\t {}".format(fn.__name__, inspect.getabsfile(fn), inspect.getsourcelines(fn)[1], ' '.join(map(str, fails))))

            return __return__
        return wrapper
    return decorator


def callCondition(fn, func, args, kwargs, extra=None):
    bound = inspect.signature(fn).bind(*args, **kwargs)
    bound.apply_defaults()
    callArgs = dict(bound.arguments)
    if extra:
        callArgs.update(extra)
    needArgs = set(inspect.getfullargspec(func).args)
    return func(**{k:v for k,v in callArgs.items() if k in needArgs})


def cacheOld(fn, args, kwargs):
    __old__ = Namespace()
    __id__ = Namespace()
    bound = inspect.signature(fn).bind(*args, **kwargs)
    bound.apply_defaults()
    for k,v in bound.arguments.items():
        __old__.__setattr__(k, copy.deepcopy(v))
        __id__.__setattr__(k, id(v))

    return __old__, __id__


def setTestMode(mode=True):
    contracts.__globals__['__testmode__'] = mode


class PreConditionError(ValueError): pass
class PostConditionError(ValueError): pass
