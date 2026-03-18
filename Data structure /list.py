#collection = single "variable"used to store multiple values 
# list = [] ordered and changeable .Duplicates ok

fruits :list[str] = ["apple", "orange", "banana", "conconut"]
#print(fruits[::-1])
#print(dir(fruits))
#print(help(fruits))
#fruits[0] = "pineapple"
#fruits.append("pineapple")
#fruits.remove("apple")
#fruits.insert(0,"di*ck")
#fruits.sort()
#fruits.reverse()
#fruits.clear()
#for fruit in fruits:
#    print(fruit)
print(fruits.index("orange"))
print(fruits.count("banana"))

