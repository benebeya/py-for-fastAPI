# TUple = () ordered and unchangeable.DUplicates OK. Faster 


fruits :tuple[str, ...] = ("apple", "orange", "banana","coconut")
#print(dir(fruits))
#print(fruits.index("orange"))
#print(fruits.count("apple"))

for fruit in fruits:
    print(fruit)