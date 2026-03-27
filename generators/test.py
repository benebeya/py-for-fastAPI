# infinite ID generator
"""we can use generator using ()
 usage : when you dont need to get all data at once """
def generate_ids():
    id = 1
    while True:
        yield id
        id += 1

gen = generate_ids()
#?Each next() resumes from where it stopped last time

print(next(gen))
print(next(gen))
print(next(gen))