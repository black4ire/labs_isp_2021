import inspect
import types
import builtins
import copy
from collections import deque

from yaml import tokens


class TomlSerializer:
    def __init__(self):
        self.builtin_fnames = [el[0] for el in
                               inspect.getmembers(builtins, inspect.isbuiltin)]
        self.builtin_cnames = [el[0] for el in
                               inspect.getmembers(builtins, inspect.isclass)]
        self.serialization_q = deque()
        self.placeholders_q = deque()
        self.ph_iter = self.generate_placeholder()
        self.current_table_key = ""

    def generate_placeholder(self):
        i = 0
        while True:
            yield f"<placeholder {i}>"
            i += 1

    def generate_key(self, *args):
        res = ""
        first_key = args[0]
        if isinstance(first_key, str):
            if not first_key:
                pass
            else:
                if ("." in first_key
                        or " " in first_key) \
                        and first_key[0] != '"' \
                        and first_key[-1] != '"':
                    res += f"\"{first_key}\"" + "."
                else:
                    res += first_key + "."
        else:
            raise TypeError("Arguments of key generator "
                            + "must be strings!")

        for el in args[1:]:
            if not isinstance(el, str):
                raise TypeError("Arguments of key generator "
                                + "must be strings!")
            if "." in el or " " in el:
                res += f"\"{el}\"."
            else:
                res += el + "."
        res = res[:-1]  # getting rid of last dot
        return res

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
            return "<None>"
        elif inspect.isclass(obj):
            if obj.__name__ in self.builtin_cnames:
                return f"<built-in class {obj.__name__}>"
            return self.expand_dict(self.cls_to_dict(obj))
        elif isinstance(obj, types.CellType):   # for closures
            return self._expand(obj.cell_contents)
        elif isinstance(obj, object):
            return self.expand_dict(self.obj_to_dict(obj))
        else:
            raise TypeError(f"Object {obj} is not TOML-parsable.")

    def expand_list(self, lst):
        # this can be either of list, tuple, set or frozenset,
        # so we add an element at the very beginning which will
        # indictate what it actually is
        tmplist = list()
        if isinstance(lst, list):
            tmplist.append("<list>")
        elif isinstance(lst, tuple):
            tmplist.append("<tuple>")
        elif isinstance(lst, set):
            tmplist.append("<set>")
        elif isinstance(lst, frozenset):
            tmplist.append("<frozenset>")
        else:
            raise ValueError(f"Cannot dump toml array from {lst}.")
        tmplist.extend(list(lst))

        for i in range(len(tmplist)):
            tmplist[i] = self._expand(tmplist[i])
            if isinstance(tmplist[i], dict):
                ph = next(self.ph_iter)
                self.placeholders_q.append((ph, tmplist[i]))
                tmplist[i] = ph

        if tmplist[0][0] == '<' and tmplist[0][-1] == '>':
            if tmplist[0][1:-1] == "frozenset":
                tmplist = frozenset(tmplist[1:])
            elif tmplist[0][1:-1] == "tuple":
                tmplist = tuple(tmplist[1:])
            elif tmplist[0][1:-1] == "set":
                tmplist = set(tmplist[1:])
            else:
                tmplist = tmplist[1:]

        return tmplist

    def expand_dict(self, dct):
        for key, val in dct.items():
            dct[key] = self._expand(val)
        return dct

    def split_key(self, full_key):
        if not isinstance(full_key, str):
            raise TypeError("Key must be a string!"
                            + f"Actual type:{type(full_key)}")
        key_seq, key_list = [], []
        dot_just_encountered = False
        complex_key_encountered = False
        ind = 0
        while ind < len(full_key):
            if dot_just_encountered:
                if key_list:
                    res = "".join(key_list).strip()
                    if not res or " " in res:
                        if not complex_key_encountered:
                            raise ValueError(f"No spaces allowed in a bare "
                                             + f"key! Key: {res}")
                    key_seq.append(res)
                else:
                    raise ValueError("Empty key encountered!")
                if full_key[ind] == '.':
                    raise ValueError(f"Double dots encountered!"
                                     + f" Key: {full_key}")
                dot_just_encountered = False
                complex_key_encountered = False
                key_list = []
                ind -= 1
            else:
                if full_key[ind] == '.':
                    dot_just_encountered = True
                elif full_key[ind] == '"':
                    if complex_key_encountered:
                        raise ValueError("Double complex key encountered!")
                    key, ind = self.parse_tstring(full_key, ind)
                    ind -= 1
                    complex_key_encountered = True
                    key_list.append(key)
                elif full_key[ind] != " " and complex_key_encountered:
                    raise ValueError("Invalid key encountered!")
                else:
                    key_list.append(full_key[ind])
            ind += 1

        if dot_just_encountered:
            raise ValueError("Dot at the end detected!")

        if key_list:
            res = "".join(key_list).strip()
            if not res:
                raise ValueError("Empty key encountered!")
            if not complex_key_encountered and " " in res:
                raise ValueError(f"No spaces allowed in a bare key!"
                                 + f" Key: {res}")
            key_seq.append(res)

        return key_seq

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

    def dumps_str(self, string):
        return '"' + string.replace("\\", r"\\").replace("\"", r"\"")\
            .replace("\r", r"\r").replace("\t", r"\t")\
            .replace("\f", r"\f").replace("\b", "\\b")\
            .replace("\n", r"\n") + '"'

    def dumps_list(self, lst):
        tmplist = list()
        if isinstance(lst, list):
            tmplist.append("<list>")
        elif isinstance(lst, tuple):
            tmplist.append("<tuple>")
        elif isinstance(lst, set):
            tmplist.append("<set>")
        elif isinstance(lst, frozenset):
            tmplist.append("<frozenset>")
        else:
            raise ValueError(f"Cannot dump toml array from {lst}.")
        tmplist.extend(list(lst))

        res = "["
        for el in tmplist:
            res += " " + self._dumps(el) + ","
        res = res[:-1]  # gettin rid of the last comma
        res += " ]"
        return res

    def dumps_dict(self, dct):
        res = ""
        full_name = self.current_table_key
        if full_name:
            res = f"[{full_name}]\n"

        for key, val in dct.items():
            if isinstance(val, dict):
                self.serialization_q.append(
                    (
                        self.generate_key(
                            *self.split_key(full_name),
                            key),
                        val)
                )
            else:
                # full_key = self.generate_key(*self.split_key(key))
                full_key = self.generate_key(key)
                res += f"{full_key} = {self._dumps(val)}\n"
        res += "\n"
        return res

    def _dumps(self, obj):
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
            return self.dumps_list(obj)
        elif isinstance(obj, dict):
            return self.dumps_dict(obj)
        elif isinstance(obj, types.FunctionType):
            return self.dumps_dict(self.func_to_dict(obj))
        elif isinstance(obj, types.BuiltinFunctionType):
            if obj.__name__ in self.builtin_fnames:
                return f"\"<built-in function {obj.__name__}>\""
            else:
                module = __import__(obj.__module__)
                module_func = getattr(module, obj.__name__)
                if module_func is not None:
                    return f"\"<{module.__name__} function" \
                        + f" {module_func.__name__}>\""
                else:
                    raise NameError(f"No function {obj.__name__} was found"
                                    + f"in module {module.__name__}")
        elif obj is None:
            return "\"<None>\""
        elif inspect.isclass(obj):
            if obj.__name__ in self.builtin_cnames:
                # built-in class, like exceptions
                return f"\"<built-in class {obj.__name__}>\""
            return self.dumps_dict(self.cls_to_dict(obj))
        elif isinstance(obj, types.CellType):   # for closures
            return self._dumps(obj.cell_contents)
        elif isinstance(obj, object):
            return self.dumps_dict(self.obj_to_dict(obj))
        else:
            raise TypeError(f"Object {obj} is not TOML-parsable.")

    def dumps(self, obj):
        toml_dict = dict()  # primitivated dictionary to convert to TOML
        obj = copy.deepcopy(obj)

        if obj is True:
            return "ttype = \"bool\"\ntvalue = true"
        elif obj is False:
            return "ttype = \"bool\"\ntvalue = false"
        elif obj is None:
            return "ttype = \"NoneType\"\ntvalue = \"<None>\""
        elif isinstance(obj, (int, float)):
            return f"ttype = \"digit\"\ntvalue = {str(obj)}"
        elif isinstance(obj, bytes):
            return "ttype = \"bytes\"\ntvalue = \"" \
                + f"{str(list(bytearray(obj)))}\""
        elif isinstance(obj, str):
            return f"ttype = \"string\"\ntvalue = {self.dumps_str(obj)}"
        elif isinstance(obj, (set, frozenset, list, tuple)):
            toml_dict["ttype"] = "array"
            toml_dict["tvalue"] = self.expand_list(obj)
        elif isinstance(obj, dict):
            toml_dict["ttype"] = "dictionary"
            toml_dict["tvalue"] = self.expand_dict(obj)
        elif isinstance(obj, types.FunctionType):
            toml_dict["ttype"] = "dictionary"
            toml_dict["tvalue"] = self.func_to_dict(obj)
        elif isinstance(obj, types.BuiltinFunctionType):
            if obj.__name__ in self.builtin_fnames:
                return "ttype = \"string\"\n\"" \
                    + f"<built-in function {obj.__name__}>\""
            else:
                module = __import__(obj.__module__)
                module_func = getattr(module, obj.__name__)
                if module_func is not None:
                    return f"ttype = \"string\"\n\"" \
                        + f"<{module.__name__} function " \
                        + f"{module_func.__name__}>\""
                else:
                    raise NameError(f"No function {obj.__name__} was found"
                                    + f"in module {module.__name__}")
        elif inspect.isclass(obj):
            toml_dict["ttype"] = "dictionary"
            if obj.__name__ in self.builtin_cnames:
                toml_dict["tvalue"] = f"<built-in class {obj.__name__}>"
            else:
                toml_dict["tvalue"] = self.cls_to_dict(obj)
        elif isinstance(obj, object):
            toml_dict["ttype"] = "dictionary"
            toml_dict["tvalue"] = self.obj_to_dict(obj)
        else:
            raise TypeError(f"Object {obj} is not TOML-parsable.")

        # things we're doing to create full TOML dictionary to be dumped
        toml_dict["placeholders"] = dict()
        while self.placeholders_q:
            el = self.placeholders_q.pop()
            toml_dict["placeholders"][el[0]] = self._expand(el[1])

        self.serialization_q.append(("", toml_dict))
        res = ""
        while self.serialization_q:
            el = self.serialization_q.pop()
            self.current_table_key = el[0]
            res += self._dumps(el[1])
        return res

    def dump(self, obj, fname):
        if not fname.endswith(".toml"):
            raise NameError("File must have .toml extension!")
        with open(fname, "a+") as fhandler:
            fhandler.write(self.dumps(obj))

    # DESERIALIZING SECTION #
    def make_special(self, string):
        if string[0] != '<' or string[-1] != '>':
            raise ValueError(f"String {string} isn't special.")

        if string[1: -1] == "None":
            return None

        tokens = string[1: -1].split()
        if len(tokens) == 2:
            if tokens[0] == 'placeholder':
                return string
            elif tokens[0] == 'module':
                return __import__(tokens[1])
        elif len(tokens) == 3:
            if tokens[0] != "recursive" and \
                    (tokens[1] == "function"
                     or tokens[1] == "class"):
                if tokens[0] == "built-in":
                    module = builtins
                else:
                    module = __import__(tokens[0])
                module_attr = getattr(module, tokens[2])
                return module_attr
            else:
                return string
        else:
            return string

    def parse_key(self, string):
        quote_counter = 0
        string = ' ' + string
        for i in range(len(string)):
            if string[i] == '=' and quote_counter % 2 == 0:
                return string[: i].strip(), i
            elif string[i] == '"' and string[i - 1] != '\\':
                quote_counter += 1
        raise KeyError(f"Unable to parse key in here: {string}")

    def _parse(self, tstr, index):
        if tstr[index] == '"':
            res, index = self.parse_tstring(tstr, index)
        elif tstr[index] == '[':
            res, index = self.parse_tarray(tstr, index)
        elif tstr[index] == 't' and tstr[index: index + 4] == "true":
            index += 4
            res = True
        elif tstr[index] == 'f' and tstr[index: index + 5] == "false":
            index += 5
            res = False
        elif tstr[index].isdigit() \
                or (
                    tstr[index] == '-'
                    or tstr[index] == '+') \
                and tstr[index + 1].isdigit():
            res, index = self.parse_tdigit(tstr, index)
        else:
            raise ValueError(f"Not a proper digit. String: {tstr}")
        return res, index

    def _evaluate(self, tstr):
        lines = tstr.split('\n')
        for i in range(len(lines)):
            lines[i] = lines[i].strip()

        table_encountered = True
        self.current_table_key = ""
        toml_dict = dict()
        if lines[0][0] == '[' and lines[0][-1] == ']':
            table_encountered = False
        for line in lines:
            if not line:  # since we splitted on a '\n'
                table_encountered = False  # signifies the end of table
            elif line[0] == '[' and line[-1] == ']':
                if table_encountered is False:
                    table_encountered = True
                    self.current_table_key = line[1:-1]
                    self.set_val(
                        toml_dict,
                        self.current_table_key,
                        dict()
                        )
                else:
                    raise KeyError("Table has been already encountered!"
                                   + f"Current table key: "
                                   + f"{self.current_table_key}")
            else:
                if '=' not in line:
                    raise ValueError("Not a key-value pair!"
                                     + f"Current line: {line}")
                key, ind = self.parse_key(line)
                strval = line[ind:].strip()  # string repr of val
                val, _ = self._parse(strval, 0)
                key = self.generate_key(
                    *self.split_key(self.current_table_key),
                    *self.split_key(key))
                self.set_val(toml_dict, key, val)

        # do things to place all placeholders where needed !!!
        if "placeholders" in toml_dict:
            toml_dict["tvalue"] = self._pullup_placeholders(
                toml_dict["tvalue"],
                toml_dict["placeholders"])
            del toml_dict["placeholders"]  # we don't need this anymore
        return toml_dict

    def _pullup_placeholders(self, val, ph_dict):
        if isinstance(val, dict):
            for key in val:
                val[key] = self._pullup_placeholders(val[key], ph_dict)
        elif isinstance(val, (tuple, list, set, frozenset)):
            val_type = type(val)
            val_lst = list(val)
            for i in range(len(val_lst)):
                val_lst[i] = self._pullup_placeholders(val_lst[i], ph_dict)
            return val_type(val_lst)
        elif isinstance(val, str):
            if not val:
                return val
            elif val[0] == '<' and val[-1] == '>':
                tokens = val[1: -1].split()
                if tokens[0] == 'placeholder':
                    ph_dict[val] = self._pullup_placeholders(
                        ph_dict[val],
                        ph_dict)
                    return ph_dict[val]
        return val

    def set_val(self, dct, full_key, val):
        key_seq = self.split_key(full_key)
        curr_dct_lvl = dct
        for key in key_seq[:-1]:
            try:
                curr_dct_lvl = curr_dct_lvl[key]
            except KeyError:
                curr_dct_lvl[key] = dict()
                curr_dct_lvl = curr_dct_lvl[key]
        key = key_seq[-1]
        curr_dct_lvl[key] = val

    def parse_tstring(self, tstr, index):
        if tstr[index] != '"':
            raise ValueError(f"This is not a string! String: {tstr}")
        end_index = index + 1

        try:
            while True:  # read everything until we get bare " symbol
                if tstr[end_index] == '\\':  # this one is for sure escaping
                    end_index += 2
                    continue
                if tstr[end_index] == '"':
                    break
                end_index += 1
        except IndexError:
            raise IndexError(f"No \" was encountered on the end of string!")

        s = tstr[index+1: end_index]
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
                    raise ValueError(f"Can't work out this escaping "
                                     + f"{s[i : i+2]}.")
                i += 1
            else:
                res.append(s[i])
            i += 1
        res = "".join(res)
        if res and res[0] == '<' and res[-1] == '>':
            res = self.make_special(res)  # if string is like "<None>"
        return res, end_index + 1

    def parse_tdigit(self, tstr, index):
        if tstr[index] != '-' and tstr[index] != '+' \
                and not tstr[index].isdigit():
            raise ValueError(f"This is not a number! Current index: {index}")

        end_index = index

        possible_digits = set([str(i) for i in range(10)])
        possible_chars = set(['.', '-', '+', 'E'])
        # these two will regulate the rules of the next appearing symbol
        e_encountered = False
        dot_encountered = False
        try:
            curr_char = tstr[end_index]
            while curr_char.upper() in possible_chars \
                    or curr_char in possible_digits:

                if not (curr_char.isdigit() or curr_char in "-+eE."):
                    raise ValueError("This is not a valid digit! " +
                                     f"Result: {tstr[index: end_index]}")

                if curr_char.upper() in possible_chars:
                    if curr_char in "-+":
                        possible_chars.clear()
                        possible_digits.update(*[str(i) for i in range(10)])
                        # nothing except digits will appear
                    elif curr_char in "eE":
                        if e_encountered:
                            raise ValueError(
                                "This is not a valid digit! " +
                                f"Result: {tstr[index: end_index]}")
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
                                f" Result: {tstr[index: end_index]}")
                    dot_encountered = True
                    possible_chars.clear()
                    possible_digits.update(*[str(i) for i in range(10)])
                    # after a dot there can only be digits

                elif curr_char in possible_digits:
                    if curr_char == '0' \
                            and end_index > 0 \
                            and not tstr[end_index - 1].isdigit():
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
                curr_char = tstr[end_index]
        except IndexError:
            end_index -= 1

        res = tstr[index: end_index + 1]
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

    def parse_tarray(self, tstr, index):
        if tstr[index] != '[':
            raise ValueError(f"This is not an array! Current index: {index}")
        end_index = index + 1

        lst = []
        comma_encountered = False
        while True:
            if tstr[end_index] == ']':
                if not comma_encountered:
                    break
                else:
                    raise ValueError("Unneeded comma at the end!"
                                     + f"String: {tstr}")
            elif tstr[end_index] == ',':
                if not comma_encountered:
                    comma_encountered = True
                    end_index += 1
                    continue
                else:
                    raise ValueError(f"Two commas in a row encountered!"
                                     + f"String: {tstr}")
            elif tstr[end_index] == ' ':
                end_index += 1
                continue

            res, end_index = self._parse(tstr, end_index)

            if len(lst) != 0:
                if comma_encountered:
                    lst.append(res)
                    comma_encountered = False
                else:
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

        if isinstance(lst[0], str) \
                and lst[0][0] == '<' \
                and lst[0][-1] == '>':
            if lst[0][1: -1] == "list":
                lst = lst[1:]
            elif lst[0][1: -1] == "tuple":
                lst = tuple(lst[1:])
            elif lst[0][1: -1] == "set":
                lst = set(lst[1:])
            elif lst[0][1: -1] == "frozenset":
                lst = frozenset(lst[1:])
            else:
                raise ValueError("Cannot understand which type "
                                 + "(list, tuple, set, frozenset)"
                                 + "to transfrom to."
                                 + f"Value: {lst}")
        return lst, end_index + 1

    # ACTUALLY GETTING DESERIALIZED OBJECT
    def dict_to_func(self, tobj):
        globs = {}
        for key, val in tobj["__globals__"].items():
            if isinstance(val, str):
                if "built-in function" in val \
                        or "built-in class" in val:
                    globs[key] = getattr(builtins, key)
                    continue
            globs[key] = self._deserialize(val)

        codeobj = self.dict_to_code(tobj["__code__"])
        fake_cells = self._make_fake_cells(tobj["__closure__"])
        res = types.FunctionType(codeobj,
                                 globs,
                                 tobj["__name__"],
                                 None,
                                 fake_cells)
        res.__defaults__ = tobj["__defaults__"] \
            if tobj["__defaults__"] is None \
            else tuple(self._deserialize(tobj["__defaults__"]))
        res.__kwdefaults__ = self._deserialize(tobj["__kwdefaults__"])
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

    def dict_to_class(self, tobj):
        bases = self.deserialize_tarr(tobj["bases"])
        return type(tobj["name"],
                    bases,
                    self.deserialize_tobj(tobj["dict"]))

    def dict_to_obj(self, tobj):
        objcls = self.dict_to_class(tobj["class"])
        res = objcls()
        res.__dict__ = self.deserialize_tobj(tobj["vars"])
        return res

    def dict_to_code(self, tobj):
        codeobj = types.CodeType(tobj["co_argcount"],
                                 tobj["co_posonlyargcount"],
                                 tobj["co_kwonlyargcount"],
                                 tobj["co_nlocals"],
                                 tobj["co_stacksize"],
                                 tobj["co_flags"],
                                 bytes(bytearray(
                                     self.parse_tarray(
                                         tobj["co_code"], 0
                                     )[0]
                                 )),
                                 self._deserialize(tobj["co_consts"]),
                                 tuple(tobj["co_names"]),
                                 tuple(tobj["co_varnames"]),
                                 tobj["co_filename"],
                                 tobj["co_name"],
                                 tobj["co_firstlineno"],
                                 bytes(bytearray(
                                     self.parse_tarray(
                                         tobj["co_lnotab"], 0
                                     )[0]
                                 )),
                                 tuple(tobj["co_freevars"]),
                                 tuple(tobj["co_cellvars"]))
        return codeobj

    def deserialize_tobj(self, tobj):
        if "co_argcount" in tobj \
                and "co_posonlyargcount" in tobj \
                and "co_kwonlyargcount" in tobj \
                and "co_nlocals" in tobj \
                and "co_stacksize" in tobj \
                and "co_flags" in tobj \
                and "co_code" in tobj \
                and "co_consts" in tobj \
                and "co_names" in tobj \
                and "co_varnames" in tobj \
                and "co_filename" in tobj \
                and "co_name" in tobj \
                and "co_firstlineno" in tobj \
                and "co_lnotab" in tobj \
                and "co_freevars" in tobj \
                and "co_cellvars" in tobj:
            res = self.dict_to_code(tobj)
        elif "__globals__" in tobj \
                and "__name__" in tobj \
                and "__code__" in tobj:
            res = self.dict_to_func(tobj)
        elif "class" in tobj \
                and "vars" in tobj:
            res = self.dict_to_obj(tobj)
        elif "name" in tobj \
                and "bases" in tobj \
                and "dict" in tobj:
            res = self.dict_to_class(tobj)
        elif "staticmethod" in tobj:
            res = staticmethod(self.dict_to_func(tobj["staticmethod"]))
        elif "classmethod" in tobj:
            res = classmethod(self.dict_to_func(tobj["classmethod"]))
        else:
            res = {}
            for key, val in tobj.items():
                res[key] = self._deserialize(val)
        return res

    def deserialize_tarr(self, tobj):
        res = []
        for el in tobj:
            res.append(self._deserialize(el))
        return type(tobj)(res)

    def _deserialize(self, tobj):
        if isinstance(tobj, dict):
            res = self.deserialize_tobj(tobj)
        elif isinstance(tobj, (list, tuple, set, frozenset)):
            res = self.deserialize_tarr(tobj)
        elif isinstance(tobj, str) and len(tobj) != 0:
            if tobj[0] == '<' and tobj[-1] == '>':
                tokens = tobj[1: -1].split(' ')
                if len(tokens) == 3:
                    module_name, type_name, name = \
                        tokens[0], tokens[1], tokens[2]

                    if "built-in" == module_name:
                        module = builtins
                        if "function" == type_name or "class" == type_name:
                            module_attr = getattr(module, name)
                            return module_attr
                    elif "recursive" == module_name:  # leave it as is
                        return tobj
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
                    res = tobj
            else:
                res = tobj
        else:
            res = tobj
        return res

    def loads(self, string):
        if not isinstance(string, str):
            raise TypeError("Argument must be a string! "
                            + f"Type: {type(string)}")
        toml_dict = self._deserialize(self._evaluate(string))
        return toml_dict["tvalue"]

    def load(self, fname):
        if not fname.endswith(".toml"):
            raise NameError("File must have .toml extension!")
        with open(fname, "r") as fhandler:
            text = fhandler.read()
            obj = self.loads(text)
            return obj
