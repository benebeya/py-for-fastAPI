def get_data () -> dict[str, int]:
    return {"a":1, "b":2}



def greet_people(people:list[str])-> None:
    for person in people:
        print(f"Hello {person.capitalize()}!")
        
greet_people(["bob", "james"])
