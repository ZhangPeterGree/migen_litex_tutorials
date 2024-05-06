#!/usr/bin/env python

# zip("abc", "def")
# print(zip("abc", "def"))
azip = zip("abc", "def")
print(f'azip is {azip}')

a, *b = zip("abc", "def")

print(f'a = {a}, b = {b},')
print(f'a is {type(a)}, b is {type(b)}')
print(len(a))


for x in a:
    print(x)