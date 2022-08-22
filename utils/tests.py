import unittest
import copy

from utils.data_structures import Dict
from utils.common import remove_empty_keys_from_dict


class TestDict(unittest.TestCase):
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
        assert sorted(d.keys()) == ['a', 'b', 'c']

    def test_remove_empty_keys_from_dict(self):
        TEST_SET = [
            ({}, {}),
            ({
                'key1': None,
                'key2': [],
                'key3': (),
                'key4': {},
            }, {}),
            (
                {'key1': {}, 'key2': 'value1'},
                {'key2': 'value1'}
            ),
            ({
                'key1': {
                    'key11': {},
                    'key2': 'value2',
                },
                'key2': 'value2',
                'sample': {
                    'sample2': {
                        'sample3': {
                        },
                    },
                },
            }, {
                'key1': {
                    'key2': 'value2',
                },
                'key2': 'value2',
            }),
        ]

        for obj, expected_obj in TEST_SET:
            original_obj = copy.deepcopy(obj)
            assert remove_empty_keys_from_dict(obj) == expected_obj
            assert original_obj == obj
