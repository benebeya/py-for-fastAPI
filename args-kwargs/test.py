# *args = allows you to pass multiple argument , they stored in  (tuple)
# **kwargs = allow you to pass keyword-argument, they stored in {dict}


def shipping_label(*args , **kwargs):
    for arg in args:
        print(arg, end = " " )
    print()
    if "state" in kwargs:
        print(f"{kwargs.get("state")} {kwargs.get("apt")}")
    else:
        print(f"{kwargs.get("apt")}")
    


shipping_label("Dr.", "med", "sidibeya",
               street = "123 Fake St.",
               apt = "#100",
               city = "nema",
               state = "MR",
               )




