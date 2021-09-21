import unittest
from serializers.packer import Packer
from unittests.test_objects import *


class SerializerTester(unittest.TestCase):
    def __init__(self, method):
        super().__init__(method)
        factory = Packer()
        self.json_serializer = factory.create_serializer("json")
        self.pickle_serializer = factory.create_serializer("pickle")
        self.toml_serializer = factory.create_serializer("toml")
        self.yaml_serializer = factory.create_serializer("yaml")

    def test_none(self):
        jobj = self.json_serializer.loads(
                self.json_serializer.dumps(none_obj))
        pobj = self.pickle_serializer.loads(
                self.pickle_serializer.dumps(none_obj))
        tobj = self.toml_serializer.loads(
                self.toml_serializer.dumps(none_obj))
        yobj = self.yaml_serializer.loads(
                self.yaml_serializer.dumps(none_obj))

        self.assertEqual(jobj, none_obj)
        self.assertEqual(pobj, none_obj)
        self.assertEqual(tobj, none_obj)
        self.assertEqual(yobj, none_obj)

    def test_iterables(self):
        jobj = self.json_serializer.loads(
                self.json_serializer.dumps(iterable_obj))
        pobj = self.pickle_serializer.loads(
                self.pickle_serializer.dumps(iterable_obj))
        tobj = self.toml_serializer.loads(
                self.toml_serializer.dumps(iterable_obj))
        yobj = self.yaml_serializer.loads(
                self.yaml_serializer.dumps(iterable_obj))

        self.assertEqual(jobj, iterable_obj)
        self.assertEqual(pobj, iterable_obj)
        self.assertEqual(tobj, iterable_obj)
        self.assertEqual(yobj, iterable_obj)

    def test_function(self):
        jobj = self.json_serializer.loads(
                self.json_serializer.dumps(fact))
        pobj = self.pickle_serializer.loads(
                self.pickle_serializer.dumps(fact))
        tobj = self.toml_serializer.loads(
                self.toml_serializer.dumps(fact))
        yobj = self.yaml_serializer.loads(
                self.yaml_serializer.dumps(fact))

        self.assertEqual(jobj(6), expected_fact_ans)
        self.assertEqual(pobj(6), expected_fact_ans)
        self.assertEqual(tobj(6), expected_fact_ans)
        self.assertEqual(yobj(6), expected_fact_ans)

    def test_lambda(self):
        jobj = self.json_serializer.loads(
                self.json_serializer.dumps(lambda_func))
        pobj = self.pickle_serializer.loads(
                self.pickle_serializer.dumps(lambda_func))
        tobj = self.toml_serializer.loads(
                self.toml_serializer.dumps(lambda_func))
        yobj = self.yaml_serializer.loads(
                self.yaml_serializer.dumps(lambda_func))

        self.assertEqual(jobj(3, 4), expected_lambda_ans)
        self.assertEqual(pobj(3, 4), expected_lambda_ans)
        self.assertEqual(tobj(3, 4), expected_lambda_ans)
        self.assertEqual(yobj(3, 4), expected_lambda_ans)

    def test_closure(self):
        times4 = mul(4)
        jobj = self.json_serializer.loads(
                self.json_serializer.dumps(times4))
        pobj = self.pickle_serializer.loads(
                self.pickle_serializer.dumps(times4))
        tobj = self.toml_serializer.loads(
                self.toml_serializer.dumps(times4))
        yobj = self.yaml_serializer.loads(
                self.yaml_serializer.dumps(times4))

        self.assertEqual(jobj(5), expected_closure_ans)
        self.assertEqual(pobj(5), expected_closure_ans)
        self.assertEqual(tobj(5), expected_closure_ans)
        self.assertEqual(yobj(5), expected_closure_ans)

    def test_class(self):
        jobj = self.json_serializer.loads(
                self.json_serializer.dumps(A))
        pobj = self.pickle_serializer.loads(
                self.pickle_serializer.dumps(A))
        tobj = self.toml_serializer.loads(
                self.toml_serializer.dumps(A))
        yobj = self.yaml_serializer.loads(
                self.yaml_serializer.dumps(A))

        self.assertEqual(jobj.cmeth(6), expected_fact_ans)
        self.assertEqual(pobj.cmeth(6), expected_fact_ans)
        self.assertEqual(tobj.cmeth(6), expected_fact_ans)
        self.assertEqual(yobj.cmeth(6), expected_fact_ans)

        self.assertEqual(jobj.smeth((1, 2, 3)), (1, 2, 3))
        self.assertEqual(pobj.smeth((1, 2, 3)), (1, 2, 3))
        self.assertEqual(tobj.smeth((1, 2, 3)), (1, 2, 3))
        self.assertEqual(yobj.smeth((1, 2, 3)), (1, 2, 3))

    def test_object(self):
        jobj = self.json_serializer.loads(
                self.json_serializer.dumps(myclass_obj))
        pobj = self.pickle_serializer.loads(
                self.pickle_serializer.dumps(myclass_obj))
        tobj = self.toml_serializer.loads(
                self.toml_serializer.dumps(myclass_obj))
        yobj = self.yaml_serializer.loads(
                self.yaml_serializer.dumps(myclass_obj))

        self.assertEqual(jobj.d.check_prop2(), myclass_obj.d.prop2)
        self.assertEqual(pobj.d.check_prop2(), myclass_obj.d.prop2)
        self.assertEqual(tobj.d.check_prop2(), myclass_obj.d.prop2)
        self.assertEqual(yobj.d.check_prop2(), myclass_obj.d.prop2)

    def test_files(self):
        self.json_serializer.dump(fact, filepath_j)
        self.pickle_serializer.dump(fact, filepath_p)
        self.toml_serializer.dump(fact, filepath_t)
        self.yaml_serializer.dump(fact, filepath_y)

        jobj = self.json_serializer.load(filepath_j)
        pobj = self.pickle_serializer.load(filepath_p)
        tobj = self.toml_serializer.load(filepath_t)
        yobj = self.yaml_serializer.load(filepath_y)

        self.assertEqual(jobj(6), expected_fact_ans)
        self.assertEqual(pobj(6), expected_fact_ans)
        self.assertEqual(tobj(6), expected_fact_ans)
        self.assertEqual(yobj(6), expected_fact_ans)

    def test_dict(self):
        jobj = self.json_serializer.loads(
                self.json_serializer.dumps(dct))
        pobj = self.pickle_serializer.loads(
                self.pickle_serializer.dumps(dct))
        tobj = self.toml_serializer.loads(
                self.toml_serializer.dumps(dct))
        yobj = self.yaml_serializer.loads(
                self.yaml_serializer.dumps(dct))

        self.assertEqual(jobj, dct)
        self.assertEqual(pobj, dct)
        self.assertEqual(tobj, dct)
        self.assertEqual(yobj, dct)

    def test_builtin_class(self):
        jobj = self.json_serializer.loads(
                self.json_serializer.dumps(ArithmeticError))
        pobj = self.pickle_serializer.loads(
                self.pickle_serializer.dumps(ArithmeticError))
        tobj = self.toml_serializer.loads(
                self.toml_serializer.dumps(ArithmeticError))
        yobj = self.yaml_serializer.loads(
                self.yaml_serializer.dumps(ArithmeticError))

        self.assertEquals(jobj, ArithmeticError)
        self.assertEquals(pobj, ArithmeticError)
        self.assertEquals(tobj, ArithmeticError)
        self.assertEquals(yobj, ArithmeticError)
