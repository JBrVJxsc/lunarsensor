import json
import logging
import os
import time
import asyncio

import aiohttp
from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse
import TSL2591

app = FastAPI()
logging.basicConfig()
log = logging.getLogger("lunarsensor")
log.level = logging.DEBUG if os.getenv("SENSOR_DEBUG") == "1" else logging.INFO


POLLING_SECONDS = 2
CLIENT = None
last_lux = 400
sensor = None
sensor_lock = asyncio.Lock()  # serialize access to the I²C bus

@app.on_event("startup")
async def startup_event():
    global CLIENT, sensor

    CLIENT = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8))
    await CLIENT.__aenter__()
    
    # Initialize the TSL2591 sensor
    try:
        sensor = TSL2591.TSL2591()
        log.info("TSL2591 sensor initialized successfully")
    except Exception as e:
        log.error(f"Failed to initialize TSL2591 sensor: {e}")
        sensor = None


@app.on_event("shutdown")
async def shutdown() -> None:
    await CLIENT.__aexit__(None, None, None)


async def make_lux_response():
    global last_lux
    try:
        lux = await read_lux()
    except Exception as exc:
        log.exception(exc)
    else:
        if lux is not None and lux != last_lux:
            log.debug(f"Sending {lux} lux")
            last_lux = lux

    return {"id": "sensor-ambient_light", "state": f"{last_lux} lx", "value": last_lux}


async def sensor_reader(request):
    while not await request.is_disconnected():
        yield {"event": "state", "data": json.dumps(await make_lux_response())}
        await asyncio.sleep(POLLING_SECONDS)

@app.get("/sensor/ambient_light")
async def sensor():
    return await make_lux_response()


@app.get("/sensor/ambient_light_tsl2561")
async def sensor_tsl2561():
    return await make_lux_response()


@app.get("/sensor/ambient_light_tsl2591")
async def sensor_tsl2591():
    return await make_lux_response()


@app.get("/events")
async def events(request: Request):
    event_generator = sensor_reader(request)
    return EventSourceResponse(event_generator)


# Do the sensor reading logic below


async def read_lux():
    if sensor is None:
        log.error("Sensor not initialized")
        return 400.0
        
    try:
        # Run the blocking I²C read in the default executor,
        # with a lock to prevent bus collisions
        async with sensor_lock:
            loop = asyncio.get_running_loop()
            lux = await loop.run_in_executor(None, lambda: float(sensor.Lux))
            # Round to nearest 50 for meaningful brightness changes
            lux = round(lux / 50) * 50
        return lux
    except Exception as e:
        log.error(f"Error reading from sensor: {e}")
        return 400.0
