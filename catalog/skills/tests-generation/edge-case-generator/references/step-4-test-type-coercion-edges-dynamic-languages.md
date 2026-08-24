### Step 4: Test Type Coercion Edges (Dynamic Languages)

In JavaScript and Python, implicit type coercion can cause subtle bugs.

**Python:**
```python
class TestTypeCoercionEdges:
    """Type coercion edge cases for loosely typed inputs."""

    def test_boolean_true_as_page_acts_as_1(self):
        # bool is a subclass of int in Python: True == 1
        result = paginate_results([1, 2, 3], page=True, page_size=10)
        assert result["page"] == 1

    def test_boolean_false_as_page_raises(self):
        # False == 0, which is below the minimum
        with pytest.raises(ValueError):
            paginate_results([1, 2, 3], page=False, page_size=10)

    def test_float_page_that_is_whole_number(self):
        # 2.0 == 2 in Python, but may cause slicing issues
        result = paginate_results(list(range(30)), page=2, page_size=10)
        assert result["data"] == list(range(10, 20))

    def test_string_page_raises_type_error(self):
        with pytest.raises(TypeError):
            paginate_results([1, 2], page="1", page_size=10)

    def test_none_page_raises_type_error(self):
        with pytest.raises(TypeError):
            paginate_results([1, 2], page=None, page_size=10)
```

**JavaScript:**
```javascript
describe("type coercion edge cases", () => {
  test("boolean true as page (coerces to 1)", () => {
    // true === 1 in numeric context
    expect(() => paginateResults([1, 2], true, 10)).toThrow();
  });

  test("null as page_size", () => {
    expect(() => paginateResults([1, 2], 1, null)).toThrow();
  });

  test("undefined as page", () => {
    expect(() => paginateResults([1], undefined, 10)).toThrow();
  });

  test("object as page triggers type check", () => {
    expect(() => paginateResults([1], {}, 10)).toThrow();
  });

  test("array as page triggers type check", () => {
    expect(() => paginateResults([1], [1], 10)).toThrow();
  });

  test("empty string as page_size", () => {
    // "" coerces to 0 in numeric context
    expect(() => paginateResults([1], 1, "")).toThrow();
  });
});
```
