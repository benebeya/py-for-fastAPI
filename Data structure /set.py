# Set = {} unordered and immutable,but add/remove OK.NO duplicates 


fruits :set[str]= {"apple", "orange", "banana","conconut","orange"}

#print(len(fruits))

fruits.add("boo")
fruits.remove("boo")
fruits.pop()

print(fruits)