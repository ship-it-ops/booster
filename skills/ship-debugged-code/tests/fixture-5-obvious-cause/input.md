# Input: a failure whose cause the error names

Set up a directory with `totals.py` and `test_totals.py` from this fixture. Do not copy this file or `expected-output.md`. Then send:

````text
fix this

```
ERROR: test_two_lines (test_totals.OrderTotalTest)
  File "totals.py", line 5, in order_total
    total += line["quantity"] * line["unit_price_cent"]
KeyError: 'unit_price_cent'
```
````
