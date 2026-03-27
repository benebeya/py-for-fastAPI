import asyncio
"""
#define the first  coroutine 
async def fetch_data (delay, id):
    print("Fetching data ....id:", id )
    await asyncio.sleep(delay)
    print("Data fetched , id:", id )
    return{"data":"some data ", "id":id}

#? define another coroutine that calls the first coroutine 
async def main ():
  
    task1 = fetch_data(4,1)# creating the coroutine obj that we need to await it 
    task2 = fetch_data(4,2)
    
    result1 = await task1
    print(f"Received result :{result1}")
    
    result2 = await task2
    print(f"Received result :{result2}")

# run the main coroutine obj
asyncio.run(main())

"""
async def fetch_data (id,sleep_time ):
    print(f"Coroutine {id } starting to fetch data .")
    await asyncio.sleep(sleep_time)# Simulate network request or IO operation
    # Return some data as a result 
    return {"id":id ,"data":f"Sample data from coroutine {id}"}


async def main ():
    tasks = []
    async with asyncio.TaskGroup() as tg :
        for i , sleep_time in enumerate([2,1,3], start=1):
            task = tg.create_task(fetch_data(i, sleep_time))
            tasks.append(task)
    
    results = [task.result() for task in tasks]
        
    for result in results:
        print(f"Recevied result: {result}")
        
# run the main coroutine 
asyncio.run(main())

