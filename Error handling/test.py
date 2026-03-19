#exception = Anevent that interrupts the flow of a program 
#            (ZeroDivisionError,TypeError,ValueError )
#           1.try, 2.except, 3.finnally 

try:
    nbre =  int(input("Entre a number :"))
    print(1/nbre)
except ZeroDivisionError:
    print("you cant divide by zero idiot !")

except ValueError :
    print("entre nbres please!")

except Exception:
    print("Something went wrong!")

finally:
    print("Do some clean up here ")#always execute 

