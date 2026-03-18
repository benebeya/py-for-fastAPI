# dictionary = a collection of {key:value }paires 
#               ordered and changeable. No duplicates 


capitals :dict[str,str] = {"USA":"Washington D.C",
            "INDIA":"New Delhi",
            "CHINA":"Beijing",
            "RUSSIA":"Moscow"}

#print(dir(capitals))
#print(help(capitals))
#print(capitals.get("FRANCE"))

#if capitals.get("RUSSIA"):
#    print("that capital exist ")
#else:
#    print("that capital doesn't exist ")

#capitals.update({"FRANCE":"PARIS"}) #! we can insert or update exist value paire 
#capitals.update({"USA":"NYC"})
#capitals.pop("INDIA")
#capitals.popitem()
#capitals.clear()

#keys =  capitals.keys()
#values = capitals.values() 
#print(f"{keys}:{values}")
#items = capitals.items()
#print(items)
#for key, value in capitals.items():
#    print(f"{key}:{value}")

#----------------------------------------------------------------------------------------
# dict comprehension = create dict using an expression 
#                   can replaced for loops and certain lambda functions
#?dictionary = {key:expression for (key,value) in iterable }

#cities_in_f = {"nyc":32,"boston":75,"LA":100}

#cities_in_C = {key:round((value-32)*(5/9)) for (key, value) in cities_in_f.items()}
#print(cities_in_C)
#?dictionary = {key:expression for (key,value) in iterable if condition }
#?dictionary = {key:(if/else) for (key,value) in iterable  }
#?dictionary = {key:function(value) for (key,value) in iterable  }
weather = {"usa":"sunny","canda":"snowing","MR":"sunny","FR":"cloudy","EN":"sunny"}
sunny_weather = {key:value for (key,value) in weather.items() if value == "sunny" }
print(sunny_weather)