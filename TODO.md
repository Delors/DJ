# 1. Function to generate entries based on alternatives

_E.g._

```python
data = [["T","t"],["i"],["r","n"],["q","Q"],["u","n","ü"],["e","é","è"]]

def print_strings(result_str,l_of_l_of_strs):
    if len(l_of_l_of_strs) == 0:
        print(result_str)
        return

    l_of_strs = l_of_l_of_strs[0]
    remaining_l_of_l_of_strs = l_of_l_of_strs[1:]

    for s in l_of_strs:
        new_result_str = result_str + s
        print_strings(new_result_str,remaining_l_of_l_of_strs)

print_strings("",data)
```

# 2. function to replace (e.g. vowles) by numbers counting them up

_E.g._ Hallo => H1ll2