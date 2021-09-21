import inspect
import types
import builtins
import copy
import math
import pickle


class PickleSerializer:
    # SERIALIZING SECTION #
    def __init__(self):
        self.builtin_fnames = [el[0] for el in
                               inspect.getmembers(builtins, inspect.isbuiltin)]
        self.builtin_cnames = [el[0] for el in
                               inspect.getmembers(builtins, inspect.isclass)]

    def _expand(self, obj):
        if obj is True:
            return True
        elif obj is False:
            return False
        elif isinstance(obj, (int, float)):
            return obj
        elif isinstance(obj, bytes):
            return str(list(bytearray(obj)))
        elif isinstance(obj, str):
            return obj
        elif isinstance(obj, (set, frozenset, list, tuple)):
            return self.expand_list(obj)
        elif isinstance(obj, dict):
            return self.expand_dict(obj)
        elif isinstance(obj, types.FunctionType):
            return self.expand_dict(self.func_to_dict(obj))
        elif isinstance(obj, types.BuiltinFunctionType):
            if obj.__name__ in self.builtin_fnames:
                return f"<built-in function {obj.__name__}>"
            else:
                module = __import__(obj.__module__)
                module_func = getattr(module, obj.__name__)
                if module_func is not None:
                    return f"<{module.__name__} function " \
                        + f"{module_func.__name__}>"
                else:
                    raise NameError(f"No function {obj.__name__} was found"
                                    + f"in module {module.__name__}")
        elif obj is None:
            return None
        elif inspect.isclass(obj):
            if obj.__name__ in self.builtin_cnames:
                return f"<built-in class {obj.__name__}>"
            return self.expand_dict(self.cls_to_dict(obj))
        elif isinstance(obj, types.CellType):   # for closures
            return self._expand(obj.cell_contents)
        elif isinstance(obj, object):
            return self.expand_dict(self.obj_to_dict(obj))
        else:
            raise TypeError(f"Object {obj} is not PICKLE-parsable.")

    def expand_list(self, lst):
        if not isinstance(lst, (tuple, list, set, frozenset)):
            raise ValueError(f"Cannot dump toml array from {lst}.")
        lst_type = type(lst)
        tmplist = list(lst)

        for i in range(len(tmplist)):
            tmplist[i] = self._expand(tmplist[i])
        return lst_type(tmplist)

    def expand_dict(self, dct):
        for key, val in dct.items():
            dct[key] = self._expand(val)
        return dct

    def cls_to_dict(self, clsobj):
        bases = []
        for base in clsobj.__bases__:
            if base.__name__ != "object":
                bases.append(self.cls_to_dict(base))
        clsdict = {}
        attrs = clsobj.__dict__
        for key in attrs:
            if inspect.isclass(attrs[key]):
                clsdict[key] = self.cls_to_dict(attrs[key])
            elif inspect.isfunction(attrs[key]):
                clsdict[key] = self.func_to_dict(attrs[key])
            elif isinstance(attrs[key], (set, frozenset, dict, list,
                                         tuple, int, float, bool,
                                         type(None), str)):
                clsdict[key] = attrs[key]
            elif isinstance(attrs[key], classmethod):
                clsdict[key] = {"classmethod":
                                self.func_to_dict(attrs[key].__func__)}
            elif isinstance(attrs[key], staticmethod):
                clsdict[key] = {"staticmethod":
                                self.func_to_dict(attrs[key].__func__)}
        return {"name": clsobj.__name__,
                "bases": self._expand(tuple(bases)),
                "dict": self._expand(clsdict)}

    def obj_to_dict(self, obj):
        if isinstance(obj, types.CodeType):
            return {"co_argcount": obj.co_argcount,
                    "co_posonlyargcount": obj.co_posonlyargcount,
                    "co_kwonlyargcount": obj.co_kwonlyargcount,
                    "co_nlocals": obj.co_nlocals,
                    "co_stacksize": obj.co_stacksize,
                    "co_flags": obj.co_flags,
                    "co_code": str(list(bytearray(obj.co_code))),
                    "co_consts": self._expand(obj.co_consts),
                    "co_names": obj.co_names,
                    "co_varnames": obj.co_varnames,
                    "co_filename": obj.co_filename,
                    "co_name": obj.co_name,
                    "co_firstlineno": obj.co_firstlineno,
                    "co_lnotab": str(list(bytearray(obj.co_lnotab))),
                    "co_freevars": self._expand(obj.co_freevars),
                    "co_cellvars": self._expand(obj.co_cellvars)}
        return {"class": self._expand(self.cls_to_dict(obj.__class__)),
                "vars": self._expand(obj.__dict__)}

    def pull_from_code_to_func_globals(self, codeobj, func=None):
        if func is None:
            return {}

        globs = {}
        for i in codeobj.co_names:
            if i in self.builtin_fnames:
                globs[i] = f"<built-in function {i}>"
            elif i in self.builtin_cnames:
                globs[i] = f"<built-in class {i}>"
            elif i in func.__globals__:
                if inspect.isclass(func.__globals__[i]):
                    globs[i] = self.cls_to_dict(func.__globals__[i])
                elif inspect.isfunction(func.__globals__[i]):
                    if func.__name__ == i:
                        globs[i] = f"<recursive function {i}>"
                        # recursion identifier
                    else:
                        globs[i] = self.func_to_dict(func.__globals__[i])
                elif inspect.ismodule(func.__globals__[i]):
                    globs[i] = f"<module {i}>"
                    # sets the module with its name
                else:
                    globs[i] = func.__globals__[i]

        for i in codeobj.co_consts:
            if isinstance(i, types.CodeType):
                globs.update(self.pull_from_code_to_func_globals(i, func))

        return globs

    def func_to_dict(self, func):
        globs = {}
        globs.update(self.pull_from_code_to_func_globals(func.__code__, func))

        return {"__globals__": self._expand(globs),
                "__name__": func.__name__,
                "__qualname__": func.__qualname__,
                "__code__": self._expand(self.obj_to_dict(func.__code__)),
                "__module__": func.__module__,
                "__annotations__": self._expand(func.__annotations__),
                "__closure__":
                self._expand(func.__closure__),
                "__defaults__":
                self._expand(func.__defaults__),
                "__kwdefaults__":
                self._expand(func.__kwdefaults__)}

    def dumps(self, obj):
        t_obj = copy.deepcopy(obj)
        return pickle.dumps(self._expand(t_obj))

    def dump(self, obj, fname):
        if not fname.endswith(".pickle"):
            raise NameError("File must have .pickle extension!")
        with open(fname, "ab+") as fhandler:
            fhandler.write(self.dumps(obj))

    # DESERIALIZING SECTION #
    def _deserialize(self, obj):
        if isinstance(obj, dict):
            res = self.deserialize_obj(obj)
        elif isinstance(obj, (list, tuple, set, frozenset)):
            res = self.deserialize_arr(obj)
        elif isinstance(obj, str) and len(obj) != 0:
            if obj[0] == '<' and obj[-1] == '>':
                tmp = obj[1: -1].split(' ')
                if len(tmp) == 3:
                    module_name, type_name, name = tmp[0], tmp[1], tmp[2]
                    if "built-in" == module_name:
                        module = builtins
                        if "function" == type_name or "class" == type_name:
                            module_attr = getattr(module, name)
                            return module_attr
                    elif "recursive" == module_name:  # leave it as is
                        return obj
                    else:
                        module = __import__(module_name)
                        module_attr = getattr(module, name)
                        return module_attr
                elif len(tmp) == 2:
                    module_name = tmp[1]
                    try:
                        module = __import__(module_name)
                        return module
                    except ModuleNotFoundError:
                        raise NameError(f"No module {module_name} "
                                        + "was found.")
                else:
                    res = obj
            else:
                res = obj
        else:
            res = obj
        return res

    def deserialize_arr(self, obj):
        res = []
        for el in obj:
            res.append(self._deserialize(el))
        return type(obj)(res)

    def deserialize_obj(self, obj):
        if "co_argcount" in obj \
                and "co_posonlyargcount" in obj \
                and "co_kwonlyargcount" in obj \
                and "co_nlocals" in obj \
                and "co_stacksize" in obj \
                and "co_flags" in obj \
                and "co_code" in obj \
                and "co_consts" in obj \
                and "co_names" in obj \
                and "co_varnames" in obj \
                and "co_filename" in obj \
                and "co_name" in obj \
                and "co_firstlineno" in obj \
                and "co_lnotab" in obj \
                and "co_freevars" in obj \
                and "co_cellvars" in obj:
            res = self.dict_to_code(obj)
        elif "__globals__" in obj \
                and "__name__" in obj \
                and "__code__" in obj:
            res = self.dict_to_func(obj)
        elif "class" in obj \
                and "vars" in obj:
            res = self.dict_to_obj(obj)
        elif "name" in obj \
                and "bases" in obj \
                and "dict" in obj:
            res = self.dict_to_class(obj)
        elif "staticmethod" in obj:
            res = staticmethod(self.dict_to_func(obj["staticmethod"]))
        elif "classmethod" in obj:
            res = classmethod(self.dict_to_func(obj["classmethod"]))
        else:
            res = {}
            for key, val in obj.items():
                res[key] = self._deserialize(val)
        return res

    def dict_to_func(self, obj):
        globs = {}
        for key, val in obj["__globals__"].items():
            if isinstance(val, str):
                if "built-in function" in val \
                        or "built-in class" in val:
                    globs[key] = getattr(builtins, key)
                    continue
            globs[key] = self._deserialize(val)

        codeobj = self.dict_to_code(obj["__code__"])
        fake_cells = self._make_fake_cells(obj["__closure__"])
        res = types.FunctionType(codeobj,
                                 globs,
                                 obj["__name__"],
                                 None,
                                 fake_cells)
        res.__defaults__ = obj["__defaults__"] \
            if obj["__defaults__"] is None \
            else tuple(self._deserialize(obj["__defaults__"]))
        res.__kwdefaults__ = self._deserialize(obj["__kwdefaults__"])
        self._add_recursion_if_needed(res)
        self._add_builtins(res)  # for unexpected issues
        return res

    def _add_builtins(self, func):
        func.__globals__["__builtins__"] = builtins

    def _make_fake_cells(self, closure_tuple):
        def make_cell(val=None):
            x = val

            def closure():
                return x
            return closure.__closure__[0]

        if closure_tuple is None:
            return None
        lst = []
        for v in closure_tuple:
            lst.append(make_cell(v))
        return tuple(lst)

    def _add_recursion_if_needed(self, func_obj):
        if (func_obj.__name__ in func_obj.__globals__.keys()):
            if inspect.ismethod(func_obj):
                func_obj.__globals__[func_obj.__name__] = func_obj.__func__
            else:
                func_obj.__globals__[func_obj.__name__] = func_obj

    def dict_to_class(self, obj):
        bases = self.deserialize_arr(obj["bases"])
        return type(obj["name"],
                    bases,
                    self.deserialize_obj(obj["dict"]))

    def dict_to_obj(self, obj):
        objcls = self.dict_to_class(obj["class"])
        res = objcls()
        res.__dict__ = self.deserialize_obj(obj["vars"])
        return res

    def dict_to_code(self, obj):
        codeobj = types.CodeType(obj["co_argcount"],
                                 obj["co_posonlyargcount"],
                                 obj["co_kwonlyargcount"],
                                 obj["co_nlocals"],
                                 obj["co_stacksize"],
                                 obj["co_flags"],
                                 bytes(bytearray(eval(obj["co_code"]))),
                                 self._deserialize(obj["co_consts"]),
                                 tuple(obj["co_names"]),
                                 tuple(obj["co_varnames"]),
                                 obj["co_filename"],
                                 obj["co_name"],
                                 obj["co_firstlineno"],
                                 bytes(bytearray(eval(obj["co_lnotab"]))),
                                 tuple(obj["co_freevars"]),
                                 tuple(obj["co_cellvars"]))
        return codeobj

    def loads(self, byte_seq):
        if not isinstance(byte_seq, bytes):
            raise TypeError("Argument must be bytes! "
                            + f"Type: {type(byte_seq)}")
        return self._deserialize(pickle.loads(byte_seq))

    def load(self, fname):
        if not fname.endswith(".pickle"):
            raise NameError("File must have .pickle extension!")
        with open(fname, "rb") as fhandler:
            byte_seq = fhandler.read()
            obj = self.loads(byte_seq)
            return obj
