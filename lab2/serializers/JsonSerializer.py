import inspect
import types
import builtins


class JsonSerializer:
    def __init__(self, indent=4):
        self._indent = indent
        self.builtin_fnames = [el[0] for el in
                               inspect.getmembers(builtins, inspect.isbuiltin)]
        self.builtin_cnames = [el[0] for el in
                               inspect.getmembers(builtins, inspect.isclass)]

    def dumps_list(self, lst, level):
        # this can be either of list, tuple, set or frozenset,
        # so we add an element at the very beginning which will
        # indictate what it actually is
        tmplst = list()
        if isinstance(lst, list):
            tmplst.append("list")
        elif isinstance(lst, tuple):
            tmplst.append("tuple")
        elif isinstance(lst, set):
            tmplst.append("set")
        elif isinstance(lst, frozenset):
            tmplst.append("frozenset")
        else:
            raise ValueError(f"Cannot dump json array from {lst}.")

        tmplst.extend(list(lst))
        curr_indent = "\n" + " " * self._indent * level
        res = curr_indent + "["
        for el in tmplst:
            res += curr_indent + self.dumps(el, level) + ","
        res = res[:-1]  # gettin rid of the last comma
        res += curr_indent + "]"
        return res

    def dumps_dict(self, dct, level):
        if len(dct) == 0:
            return "{}"
        curr_indent = "\n" + " " * self._indent * level
        res = curr_indent + "{"
        for key in dct.keys():
            res += curr_indent + f"\"{str(key)}\" : " \
                + self.dumps(dct[key], level) + ","
        res = res[:-1]  # getting rid of the last comma
        res += curr_indent + "}"
        return res

    def dumps_str(self, string):
        return '"' + string.replace("\\", r"\\").replace("\"", r"\"")\
            .replace("\r", r"\r").replace("\t", r"\t")\
            .replace("\f", r"\f").replace("\b", "\\b")\
            .replace("\n", r"\n") + '"'

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

        return {"__globals__": globs,
                "__name__": func.__name__,
                "__qualname__": func.__qualname__,
                "__code__": self.obj_to_dict(func.__code__),
                "__module__": func.__module__,
                "__annotations__": func.__annotations__,
                "__closure__": func.__closure__,
                "__defaults__": func.__defaults__,
                "__kwdefaults__": func.__kwdefaults__}

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
                "bases": tuple(bases),
                "dict": clsdict}

    def obj_to_dict(self, obj):
        if isinstance(obj, types.CodeType):
            return {"co_argcount": obj.co_argcount,
                    "co_posonlyargcount": obj.co_posonlyargcount,
                    "co_kwonlyargcount": obj.co_kwonlyargcount,
                    "co_nlocals": obj.co_nlocals,
                    "co_stacksize": obj.co_stacksize,
                    "co_flags": obj.co_flags,
                    "co_code": obj.co_code,
                    "co_consts": obj.co_consts,
                    "co_names": obj.co_names,
                    "co_varnames": obj.co_varnames,
                    "co_filename": obj.co_filename,
                    "co_name": obj.co_name,
                    "co_firstlineno": obj.co_firstlineno,
                    "co_lnotab": obj.co_lnotab,
                    "co_freevars": obj.co_freevars,
                    "co_cellvars": obj.co_cellvars}
        return {"class": self.cls_to_dict(obj.__class__), "vars": obj.__dict__}

    def dumps(self, obj, level=-1):
        # So, this is a complex object, which can be one of 3 different types:
        #     1. Function (lambdas included)
        #     2. Object (simple or complex, idc)
        #     3. Class (type nested from object)
        # JSON supports simple parsing for these things:
        #     1. Strings
        #     2. Numbers (10, 1.5, -30, 1.2e10)
        #     3. Booleans (true, false)
        #     4. None (null)
        #     5. Array <or list> ([1,2,"hello"])
        #     6. Objects(!) <in our case dictionaries> {"key" : "value",
        #       "age" : 30}
        if obj is True:
            return "true"
        elif obj is False:
            return "false"
        elif isinstance(obj, (int, float)):
            return str(obj)
        elif isinstance(obj, bytes):
            return f"\"{str(list(bytearray(obj)))}\""
        elif isinstance(obj, str):
            return self.dumps_str(obj)
        elif isinstance(obj, (set, frozenset, list, tuple)):
            return self.dumps_list(obj, level + 1)
        elif isinstance(obj, dict):
            return self.dumps_dict(obj, level + 1)
        elif isinstance(obj, types.FunctionType):
            return self.dumps_dict(self.func_to_dict(obj), level + 1)
        elif isinstance(obj, types.BuiltinFunctionType):
            if obj.__name__ in self.builtin_fnames:
                return f"\"<built-in function {obj.__name__}>\""
            else:
                module = __import__(obj.__module__)
                module_func = getattr(module, obj.__name__)
                if module_func is not None:
                    return f"\"<{module.__name__} function " \
                        + f"{module_func.__name__}>\""
                else:
                    raise NameError(f"No function {obj.__name__} was found"
                                    + f"in module {module.__name__}")
        elif obj is None:
            return "null"
        elif inspect.isclass(obj):
            if obj.__name__ in self.builtin_cnames:
                # built-in class, like exceptions
                return f"\"<built-in class {obj.__name__}>\""
            return self.dumps_dict(self.cls_to_dict(obj), level + 1)
        elif isinstance(obj, types.CellType):   # for closures
            return self.dumps(obj.cell_contents)
        elif isinstance(obj, object):
            return self.dumps_dict(self.obj_to_dict(obj), level + 1)
        else:
            raise TypeError(f"Object {obj} is not JSON-parsable.")

    def dump(self, obj, fname):
        if not fname.endswith(".json"):
            raise AttributeError("File must have .json extension!")
        with open(fname, "w") as fhandler:
            fhandler.write(self.dumps(obj))

    def _exception_notify(self, jstr, index):
        if index >= 10:
            print(f"Surroundings: {jstr[index - 10 : index + 10]}")
        else:
            print(f"Surroundings: {jstr[0 : index + 10]}")
        print(f"The actual symbol: {jstr[index]}")

    # EVALUATING THE JSON STRING
    def _parse(self, jstr, index):
        if jstr[index] == '"':
            res, index = self.parse_jstring(jstr, index)
        elif jstr[index] == '[':
            res, index = self.parse_jarray(jstr, index)
        elif jstr[index] == '{':
            res, index = self.parse_jdict(jstr, index)
        elif jstr[index] == 't' and jstr[index: index + 4] == "true":
            index += 4
            res = True
        elif jstr[index] == 'f' and jstr[index: index + 5] == "false":
            index += 5
            res = False
        elif jstr[index] == 'n' and jstr[index: index + 4] == "null":
            index += 4
            res = None
        elif jstr[index].isdigit() or jstr[index] == '-'\
                and jstr[index + 1].isdigit():
            res, index = self.parse_jdigit(jstr, index)
        else:
            self._exception_notify(jstr, index)
            raise ValueError(f"Something is not parsable at index {index}")
        return res, index

    def parse_jstring(self, jstr, index):
        if jstr[index] != '"':
            self._exception_notify(jstr, index)
            raise ValueError(f"This is not a string! Current index: {index}")
        end_index = index + 1

        try:
            while True:  # read everything until we get bare " symbol
                if jstr[end_index] == '\\':  # this one is for sure escaping
                    end_index += 2
                    continue
                if jstr[end_index] == '"':
                    break
                end_index += 1
        except IndexError:
            raise IndexError(f"No \" was encountered on the end of string!")

        s = jstr[index + 1: end_index]
        # working on escaping symblos
        res, n, i = [], len(s), 0
        while i < n:
            if s[i] == "\\":
                if i + 1 == n:
                    break
                if s[i + 1] == "\\":
                    res.append("\\")
                elif s[i + 1] == "n":
                    res.append("\n")
                elif s[i + 1] == "r":
                    res.append("\r")
                elif s[i + 1] == "t":
                    res.append("\t")
                elif s[i + 1] == '"':
                    res.append('"')
                elif s[i + 1] == "b":
                    res.append("\b")
                elif s[i + 1] == "f":
                    res.append("\f")
                elif s[i + 1] == "/":
                    res.append("/")
                else:
                    raise ValueError("Can't work out this escaping "
                                     + f"{s[i : i + 2]}.")
                i += 1
            else:
                res.append(s[i])
            i += 1
        res = "".join(res)
        return res, end_index + 1

    def parse_jdigit(self, jstr, index):
        if jstr[index] != '-' \
                and not jstr[index].isdigit():
            self._exception_notify(jstr, index)
            raise ValueError(f"This is not a number! Current index: {index}")

        end_index = index

        possible_digits = set([str(i) for i in range(10)])
        possible_chars = set(['.', '-', 'E'])
        # these two will regulate the rules of the next appearing symbol
        e_encountered = False
        dot_encountered = False
        try:
            curr_char = jstr[end_index]
            while curr_char.upper() in possible_chars \
                    or curr_char in possible_digits:

                if not (curr_char.isdigit() or curr_char in "-+eE."):
                    raise ValueError("This is not a valid digit! " +
                                     f"Result: {jstr[index: end_index]}")

                if curr_char.upper() in possible_chars:
                    if curr_char in "-+":
                        possible_chars.clear()
                        possible_digits.update(*[str(i) for i in range(10)])
                        # nothing except digits will appear
                    elif curr_char in "eE":
                        if e_encountered:
                            raise ValueError(
                                "This is not a valid digit! " +
                                f"Result: {jstr[index: end_index]}")
                        e_encountered = True
                        try:
                            possible_chars.remove('E')
                            possible_chars.remove('.')
                        except KeyError:
                            pass
                        possible_chars.add('+')
                        possible_chars.add('-')
                        # after E there can only be sign or digit
                    elif curr_char == '.':
                        if dot_encountered:
                            raise ValueError(
                                "This is not a valid digit!" +
                                f" Result: {jstr[index: end_index]}")
                    dot_encountered = True
                    possible_chars.clear()
                    possible_digits.update(*[str(i) for i in range(10)])
                    # after a dot there can only be digits

                elif curr_char in possible_digits:
                    if curr_char == '0' \
                            and end_index > 0 \
                            and not jstr[end_index - 1].isdigit():
                        if 'E' in possible_chars:
                            possible_digits.clear()
                    if not e_encountered:
                        possible_chars.add('E')
                    if not dot_encountered:
                        possible_chars.add('.')
                    try:
                        possible_chars.remove('-')
                        possible_chars.remove('+')
                    except KeyError:
                        pass
                end_index += 1
                curr_char = jstr[end_index]
        except IndexError:
            end_index -= 1

        res = jstr[index: end_index + 1]
        if not res[-1].isdigit() and not res[-1] in "-+eE.":
            res = res[: -1]
            end_index -= 1

        type_of_digit = int
        if not res:
            raise ValueError(f"This is not a valid digit! Result: {res}")
        if any(map(lambda x: x in res, ['.', 'e', 'E'])):
            type_of_digit = float
        if len(res) > 2:
            if res[0] in "-+":
                if res[1] == '0' and res[2].isdigit() and res[2] != '0':
                    raise ValueError("This is not a valid digit!" +
                                     f" Result: {res}")
        elif len(res) == 2:
            if res[0] == '0' and res[1].isdigit() and res[1] != '0':
                raise ValueError(f"This is not a valid digit! Result: {res}")

        if res[-1] in "-+eE." or res[0] in "eE" or res[0: 2] == "00":
            raise ValueError(f"This is not a valid digit! Result: {res}")
        return type_of_digit(res), end_index + 1

    def parse_jarray(self, jstr, index):
        if jstr[index] != '[':
            self._exception_notify(jstr, index)
            raise ValueError(f"This is not an array! Current index: {index}")
        end_index = index + 1

        lst = []
        comma_encountered = False
        while True:
            if jstr[end_index] == ']':
                if not comma_encountered:
                    break
                else:
                    self._exception_notify(jstr, end_index)
                    raise ValueError("Unneeded comma at the end!"
                                     + f"Current index: {end_index}")
            elif jstr[end_index] == ',':
                if not comma_encountered:
                    comma_encountered = True
                    end_index += 1
                    continue
                else:
                    self._exception_notify(jstr, end_index)
                    raise ValueError(f"Two commas in a row encountered!"
                                     + f"Current index: {end_index}")
            elif jstr[end_index] == '\n' or jstr[end_index] == ' ':
                end_index += 1
                continue

            res, end_index = self._parse(jstr, end_index)

            if len(lst) != 0:
                if comma_encountered:
                    lst.append(res)
                    comma_encountered = False
                else:
                    self._exception_notify(jstr, end_index)
                    raise ValueError("One of elements in array is "
                                     + "not json parsable!"
                                     + f"Current index: {end_index}")
            else:
                lst.append(res)
        # On this stage we have the fully parsed array.
        # Now, we want to transfrom it to type needed.
        # Don't forget to get rid of the first element! (if it exists)
        if not lst:
            return lst, index + 1

        if isinstance(lst[0], str):
            if lst[0] == "list":
                lst = lst[1:]
            elif lst[0] == "tuple":
                lst = tuple(lst[1:])
            elif lst[0] == "set":
                lst = set(lst[1:])
            elif lst[0] == "frozenset":
                lst = frozenset(lst[1:])
            else:
                raise ValueError("Cannot understand which type "
                                 + "(list, tuple, set, frozenset)"
                                 + "to transfrom to."
                                 + f"Value: {lst}")
        return lst, end_index + 1

    def parse_jdict(self, jstr, index):
        if jstr[index] != '{':
            self._exception_notify(jstr, index)
            raise ValueError("This is not a dictionary!"
                             + f"Current index: {index}")
        end_index = index + 1
        if jstr[end_index] == '}':
            return dict(), end_index + 1

        dct = {}
        comma_encountered, colon_encountered = False, False
        key, val = None, None
        while True:
            if jstr[end_index] == '}':
                if not (comma_encountered and colon_encountered):
                    break
                else:
                    self._exception_notify(jstr, end_index)
                    raise ValueError("Unneeded comma or colon at the end!"
                                     + f"Current index: {end_index}")
            elif jstr[end_index] == ',':
                comma_encountered = True
                end_index += 1
                continue
            elif jstr[end_index] == ':':
                if key is not None:
                    colon_encountered = True
                    end_index += 1
                    continue
                else:
                    self._exception_notify(jstr, end_index)
                    raise ValueError("Colon encountered before "
                                     + "the key appeared!"
                                     + f"Current index: {end_index}")
            elif jstr[end_index] == '\n' or jstr[end_index] == ' ':
                end_index += 1
                continue

            if key is None and not colon_encountered:
                key, end_index = self.parse_jstring(jstr, end_index)
                # this can only be a string
                continue

            if key is not None and colon_encountered:
                val, end_index = self._parse(jstr, end_index)
                # this can be anything
                colon_encountered = False
            if len(dct) != 0:
                if comma_encountered:
                    dct[key] = val
                    comma_encountered = False
                else:
                    self._exception_notify(jstr, end_index)
                    raise ValueError("No comma was encountered!"
                                     + f"Current index: {end_index}")
            else:
                dct[key] = val
            key, val = None, None
        # on this stage we have the fully parsed dictionary
        return dct, end_index + 1

    # this evaluates the json string into python primitives
    # (dict, str, bool, ...)
    def _evaluate(self, jstr):
        res = None
        curr_index = 0
        while True:
            if jstr[curr_index] == '\n' or jstr[curr_index] == ' ':
                curr_index += 1
            else:
                break
        res, _ = self._parse(jstr, curr_index)
        return res

    # ACTUALLY GETTING DESERIALIZED OBJECT
    def dict_to_func(self, jsonobj):
        globs = {}
        for key, val in jsonobj["__globals__"].items():
            if isinstance(val, str):
                if "built-in function" in val \
                        or "built-in class" in val:
                    globs[key] = getattr(builtins, key)
                    continue
            globs[key] = self._deserialize(val)

        codeobj = self.dict_to_code(jsonobj["__code__"])
        fake_cells = self._make_fake_cells(jsonobj["__closure__"])
        res = types.FunctionType(codeobj,
                                 globs,
                                 jsonobj["__name__"],
                                 None,
                                 fake_cells)
        res.__defaults__ = jsonobj["__defaults__"] \
            if jsonobj["__defaults__"] is None \
            else tuple(self._deserialize(jsonobj["__defaults__"]))
        res.__kwdefaults__ = self._deserialize(jsonobj["__kwdefaults__"])
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

    def dict_to_class(self, jsonobj):
        bases = self.deserialize_jarr(jsonobj["bases"])
        return type(jsonobj["name"],
                    bases,
                    self.deserialize_jobj(jsonobj["dict"]))

    def dict_to_obj(self, jsonobj):
        objcls = self.dict_to_class(jsonobj["class"])
        res = objcls()
        res.__dict__ = self.deserialize_jobj(jsonobj["vars"])
        return res

    def dict_to_code(self, jsonobj):
        codeobj = types.CodeType(jsonobj["co_argcount"],
                                 jsonobj["co_posonlyargcount"],
                                 jsonobj["co_kwonlyargcount"],
                                 jsonobj["co_nlocals"],
                                 jsonobj["co_stacksize"],
                                 jsonobj["co_flags"],
                                 bytes(bytearray(
                                     self.parse_jarray(
                                         jsonobj["co_code"], 0
                                     )[0]
                                 )),
                                 self._deserialize(jsonobj["co_consts"]),
                                 tuple(jsonobj["co_names"]),
                                 tuple(jsonobj["co_varnames"]),
                                 jsonobj["co_filename"],
                                 jsonobj["co_name"],
                                 jsonobj["co_firstlineno"],
                                 bytes(bytearray(
                                     self.parse_jarray(
                                         jsonobj["co_lnotab"], 0
                                     )[0]
                                 )),
                                 tuple(jsonobj["co_freevars"]),
                                 tuple(jsonobj["co_cellvars"]))
        return codeobj

    def deserialize_jobj(self, jsonobj):
        if "co_argcount" in jsonobj \
                and "co_posonlyargcount" in jsonobj \
                and "co_kwonlyargcount" in jsonobj \
                and "co_nlocals" in jsonobj \
                and "co_stacksize" in jsonobj \
                and "co_flags" in jsonobj \
                and "co_code" in jsonobj \
                and "co_consts" in jsonobj \
                and "co_names" in jsonobj \
                and "co_varnames" in jsonobj \
                and "co_filename" in jsonobj \
                and "co_name" in jsonobj \
                and "co_firstlineno" in jsonobj \
                and "co_lnotab" in jsonobj \
                and "co_freevars" in jsonobj \
                and "co_cellvars" in jsonobj:
            res = self.dict_to_code(jsonobj)
        elif "__globals__" in jsonobj \
                and "__name__" in jsonobj \
                and "__code__" in jsonobj:
            res = self.dict_to_func(jsonobj)
        elif "class" in jsonobj \
                and "vars" in jsonobj:
            res = self.dict_to_obj(jsonobj)
        elif "name" in jsonobj \
                and "bases" in jsonobj \
                and "dict" in jsonobj:
            res = self.dict_to_class(jsonobj)
        elif "staticmethod" in jsonobj:
            res = staticmethod(self.dict_to_func(jsonobj["staticmethod"]))
        elif "classmethod" in jsonobj:
            res = classmethod(self.dict_to_func(jsonobj["classmethod"]))
        else:
            res = {}
            for key, val in jsonobj.items():
                res[key] = self._deserialize(val)

        return res

    def deserialize_jarr(self, jsonobj):
        res = []
        for el in jsonobj:
            res.append(self._deserialize(el))
        return type(jsonobj)(res)

    def _deserialize(self, jsonobj):
        if isinstance(jsonobj, dict):
            res = self.deserialize_jobj(jsonobj)
        elif isinstance(jsonobj, (list, tuple, set, frozenset)):
            res = self.deserialize_jarr(jsonobj)
        elif isinstance(jsonobj, str) and len(jsonobj) != 0:
            if jsonobj[0] == '<' and jsonobj[-1] == '>':
                tokens = jsonobj[1: -1].split(' ')
                if len(tokens) == 3:
                    module_name, type_name, name = \
                        tokens[0], tokens[1], tokens[2]

                    if "built-in" == module_name:
                        module = builtins
                        if "function" == type_name or "class" == type_name:
                            module_attr = getattr(module, name)
                            return module_attr
                    elif "recursive" == module_name:  # leave it as is
                        return jsonobj
                    else:
                        module = __import__(module_name)
                        module_attr = getattr(module, name)
                        return module_attr
                elif len(tokens) == 2:
                    module_name = tokens[1]
                    try:
                        module = __import__(module_name)
                        return module
                    except ModuleNotFoundError:
                        raise NameError(f"No module {module_name} "
                                        + "was found.")
                else:
                    res = jsonobj
            else:
                res = jsonobj
        else:
            res = jsonobj
        return res

    def loads(self, string):
        if not isinstance(string, str):
            raise TypeError("Argument must be a string! "
                            + f"Type: {type(string)}")
        return self._deserialize(self._evaluate(string))

    def load(self, fname):
        if not fname.endswith(".json"):
            raise NameError("File must have .json extension!")
        with open(fname, "r") as fhandler:
            text = fhandler.read()
            obj = self.loads(text)
            return obj


def main():
    json = JsonSerializer(2)
    s = json.dumps(ArithmeticError)
    print(s)


if __name__ == "__main__":
    main()
