import unittests
import unittest

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(unittests)
    unittest.TextTestRunner(verbosity=2).run(suite)
