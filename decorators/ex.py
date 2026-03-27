"""A decorator wraps a function to add extra behavior"""

def my_decorator(func):
    def wrapper():
        print("before")
        func()
        print("after")
    return wrapper

@my_decorator
def say_hello():
    print("hello!")
    
say_hello()