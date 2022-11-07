import unittest

from project.change_log import (
    get_flat_dict_diff,
    get_list_diff,
)


class ProjectChangeLog(unittest.TestCase):
    def test_get_flat_dict_diff(self):
        def _obj(value1, value2, value3):
            return dict(
                key1=value1,
                key2=value2,
                key3=value3,
            )

        list1 = [
            _obj('a', 'b', 'c'),
            _obj('b', 'c', 'd'),
            _obj('a', 'b', 'z'),
        ]
        list2 = [
            _obj('a', 'b', 'c'),
            _obj('b', 'c', 'f'),
            _obj('a', 'b', 'i'),
        ]
        diff = get_flat_dict_diff(
            list1,
            list2,
            fields=('key1', 'key2', 'key3'),
        )
        assert diff == {
            'add': [
                _obj('a', 'b', 'i'),
                _obj('b', 'c', 'f'),
            ],
            'remove': [
                _obj('a', 'b', 'z'),
                _obj('b', 'c', 'd'),
            ],
        }

    def test_get_list_diff(self):
        list1 = [1, 2, 3]
        list2 = [5, 4, 3]
        diff = get_list_diff(list1, list2)
        assert diff == {
            'add': [4, 5],
            'remove': [1, 2],
        }

        list1 = ['dfs', 'deep']
        list2 = ['toggle', 'deep', 'nepal']
        diff = get_list_diff(list1, list2)
        assert diff == {
            'add': ['nepal', 'toggle'],
            'remove': ['dfs'],
        }
