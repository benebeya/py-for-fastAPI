from pydantic import BaseModel, EmailStr, field_validator


class User(BaseModel):
    name:str
    email:EmailStr
    account_id:int 
    
    @field_validator("account_id")
    def validate_account_id(cls,value ):
        if value <= 0:
            raise ValueError(f"account_id must be positive:{value}")
        return value
    

user = User(name="med",
            email="med@estin.dz",
            account_id=1205)

#print(user)
#?To serialize your Pydantic model to JSON:
print(user.model_dump())#dict = Python data
print(user.model_dump_json())#JSON = string to send/store data

#!Convert JSON → Pydantic model (inverse)
json_data = '{"name":"med","email":"med@estin.dz","account_id":1205}'
user_js = user.model_validate_json(json_data)
print(user_js)