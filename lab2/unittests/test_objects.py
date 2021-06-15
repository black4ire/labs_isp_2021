import math


# for test_none()
none_obj = None


# for test_iterables()
iterable_obj = ("me be tuple", 3.5,
                [
                    AssertionError,
                    print,
                    set([
                        math.sin,
                        None,
                        frozenset([2, 3, 4])
                        ])
                    ]
                )


# for test_function()
def fact(a):
    if a < 2:
        return 1
    return a * fact(a - 1)


# for test_lambda()
lambda_func = lambda x, y: x**y
expected_lambda_ans = 81


# for test_closure()
def mul(a):  # closure
    def helper(b):
        return a*b
    return helper


expected_closure_ans = 20


# for test_class() and test_object()
class A:
    def __init__(self):
        self.prop1 = 7
        self.prop2 = [12, 13, 14]

    @classmethod
    def fact(cls, a):
        if a < 2:
            return 1
        return a * cls.fact(a - 1)

    @classmethod
    def cmeth(cls, b):
        return cls.fact(b)

    @staticmethod
    def smeth(a):
        return a

    def check_prop2(self):
        return self.prop2


class MyClass:
    def __init__(self):
        self.a = 5
        self.b = "string"
        self.c = (3, 2, [23, "another string"],)
        self.d = A()


myclass_obj = MyClass()


# for test_files()
filepath_j = "./unittests/dumpings/fact.json"
filepath_t = "./unittests/dumpings/fact.toml"
filepath_p = "./unittests/dumpings/fact.pickle"
filepath_y = "./unittests/dumpings/fact.yaml"
expected_fact_ans = 720

# for test_dict()
dct = {
        "builtin_class": ArithmeticError,
        "func": eval,
        "weirdness":
        (
            [
                "string",
                print,
                {
                    "key 1": 59,
                    "key2": math.sin,
                    "key.3": "more weirdness.."
                }
            ]
        )
    }
