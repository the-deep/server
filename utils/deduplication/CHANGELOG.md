## Version 1.0.5
- Add functions:
    - `index_exists(index_name: str, es: Es) -> bool`
    - `create_knn_vector_index_if_not_exists(index_name: str, vector_size: int, es: Es) -> Tuple[bool, ErrorString]`
    - `create_knn_vector_index(index_name: str, vector_size: int, es: Es, ignore_error: bool = False) -> Tuple[bool, ErrorString]`
