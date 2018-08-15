import unittest

from utils.data_structures import Dict


class TestDict(unittest.TestCase):
    def setUp(self):
        pass

    def test_creation(self):
        d = Dict(a=1, b=2)
        assert isinstance(d, Dict)
        assert isinstance(d, dict)
        d = Dict({'a': 1, 'b': 2})
        assert isinstance(d, Dict)
        assert isinstance(d, dict)

    def test_access(self):
        d = Dict(a=1, b=2)
        assert d.a == 1
        assert d.b == 2
        assert d['a'] == d.a
        assert d['b'] == d.b

    def test_set(self):
        d = Dict()
        d.b = 3
        assert d['b'] == 3
        d['c'] = 4
        assert d.c == 4

    def test_nested(self):
        d = Dict(a=Dict(b=1, c=2), b=3, c=4)
        assert isinstance(d.a, Dict)
        assert d.a.b == 1
        assert d.a.c == 2
        assert d.b == 3
        assert d['a']['b'] == 1
        d = Dict({'a': {'b': 1, 'c': 2}, 'b': 3, 'c': 4})
        assert isinstance(d.a, Dict)
        assert d.a.b == 1
        assert d.a.c == 2
        assert d.b == 3
        assert d['a']['b'] == 1

    def test_other_methods(self):
        d = Dict(a=2, b=3, c=Dict(a=1))
        assert d.keys() == ['a', 'b', 'c']
