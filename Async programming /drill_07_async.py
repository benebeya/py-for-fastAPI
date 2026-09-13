"""DRILL 07 — ASYNC   run: uv run "Async programming /drill_07_async.py" """
import asyncio, time
clock = time.perf_counter

async def fetch(id, t):
    await asyncio.sleep(t)                       # stands in for a network call
    return {"id": id}

# 1. *** YOUR COMMENTED-OUT BLOCK'S BUG *** — calling an async fn returns a COROUTINE
#    OBJECT; nothing runs. Awaiting them one at a time is just sequential code.
async def sequential():
    t1, t2 = fetch(1, .3), fetch(2, .3)          # no execution yet
    await t1; await t2                           # .3 then another .3
async def concurrent():
    await asyncio.gather(fetch(1,.3), fetch(2,.3))   # both at once
async def demo1():
    for name, fn in [("sequential", sequential), ("gather", concurrent)]:
        t0 = clock(); await fn(); print(f"1  {name:11}: {clock()-t0:.2f}s")
asyncio.run(demo1())

# 2. RUNNING THINGS AT ONCE — gather returns in ARGUMENT order, not finish order
async def demo2():
    r = await asyncio.gather(fetch(1,.2), fetch(2,.1))
    print("2  gather order preserved:", [x["id"] for x in r])
    async with asyncio.TaskGroup() as tg:        # 3.11+, the best default:
        ts = [tg.create_task(fetch(i,.1)) for i in range(3)]
    print("2  TaskGroup:", [t.result()["id"] for t in ts])   # any failure cancels the rest
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(boom("a")); tg.create_task(boom("b"))
    except* ValueError as eg:                    # note the STAR: two failed at once
        print("2  ExceptionGroup:", [str(e) for e in eg.exceptions])
async def boom(m): raise ValueError(m)
asyncio.run(demo2())

# 3. *** BLOCKING THE EVENT LOOP — the production incident ***
#    One thread. A blocking call freezes EVERY other request.
async def demo3():
    async def ok():  await asyncio.sleep(.2)     # yields control
    async def bad(): time.sleep(.2)              # BLOCKS everything, no await
    for name, fn in [("async sleep", ok), ("blocking sleep", bad)]:
        t0 = clock(); await asyncio.gather(fn(), fn(), fn())
        print(f"3  3x {name:15}: {clock()-t0:.2f}s")
    t0 = clock(); await asyncio.gather(*(asyncio.to_thread(time.sleep,.2) for _ in range(3)))
    print(f"3  3x via to_thread   : {clock()-t0:.2f}s")     # the fix
asyncio.run(demo3())
# `requests` BLOCKS -> use httpx.AsyncClient. psycopg2/sqlite3 block -> use
# asyncpg/aiosqlite, or make the endpoint plain `def`.

# 4. *** def vs async def IN FASTAPI ***
#    async def -> runs ON the event loop. Fast, but NEVER block inside it.
#    def       -> FastAPI runs it in a THREAD POOL. Blocking is safe here.
#    Worst case is async def + blocking calls, i.e. section 3. Your api.py:16 is
#    `async def` with no await in the body — harmless now, a live incident once a
#    blocking DB call goes in.

# 5. TIMEOUT, CANCELLATION, BACKPRESSURE
async def demo5():
    try:
        async with asyncio.timeout(.1): await fetch(1, 5)
    except TimeoutError: print("5  timeout fired")
    sem = asyncio.Semaphore(3); peak = active = 0
    async def limited():
        nonlocal peak, active
        async with sem:                          # a context manager again
            active += 1; peak = max(peak, active); await asyncio.sleep(.05); active -= 1
    await asyncio.gather(*(limited() for _ in range(12)))
    print(f"5  12 tasks, peak concurrency {peak} (cap 3)")
asyncio.run(demo5())
# On cancel: catch asyncio.CancelledError, clean up, then ALWAYS re-raise.

# ===================== EXERCISES — fill in, then uncomment =====================
async def e1():                         # E1 make this ~.2s, not ~.6s, same order
    a = await fetch(1,.2); b = await fetch(2,.2); c = await fetch(3,.2); return [a,b,c]
# t0=clock(); r=asyncio.run(e1()); assert clock()-t0 < .35 and [x["id"] for x in r]==[1,2,3]

async def fetch_all(ids): pass          # E2 TaskGroup, results in id order
# assert [x["id"] for x in asyncio.run(fetch_all([1,2,3]))] == [1,2,3]

async def safe(id, t, timeout): pass    # E3 result, or "timeout"
# assert asyncio.run(safe(1,.05,.5))["id"] == 1 and asyncio.run(safe(1,1,.1)) == "timeout"

def blocking(s): time.sleep(.1); return s.upper()
async def e4(items): return [blocking(i) for i in items]   # E4 fix without removing blocking()
# t0=clock(); r=asyncio.run(e4(["a","b","c"])); assert clock()-t0 < .2 and r==["A","B","C"]

# E5 async generator stream_rows(n), consumed with `async for` (Drill 06 §5)
