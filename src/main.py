# Websocket example
import asyncio
import json
from enum import Enum
from typing import Callable

from websockets.server import serve

from api import (
    line_follower_read,
    measure_distance,
    set_motor_speed,
    set_steering,
)

WEBSOCKET_PORT = 8765


class SOCKET_MESSAGE_TYPE(Enum):
    GET_DISTANCE_SENSOR = 1
    GET_LINE_SENSOR = 2
    SET_STEERING_OUTPUT = 3
    SET_MOTOR_OUTPUT = 4


MESSAGE_DICT: dict[int, dict["str", Callable | None]] = {
    SOCKET_MESSAGE_TYPE.GET_DISTANCE_SENSOR.value: {"callback": measure_distance},
    SOCKET_MESSAGE_TYPE.GET_LINE_SENSOR.value: {"callback": line_follower_read},
    SOCKET_MESSAGE_TYPE.SET_STEERING_OUTPUT.value: {"callback": set_steering},
    SOCKET_MESSAGE_TYPE.SET_MOTOR_OUTPUT.value: {"callback": set_motor_speed},
}


async def socket_handler(
    websocket,
):
    async for message in websocket:
        print(f"Message: {message}")
        inputDict = json.loads(message)
        output = None
        if "function" in inputDict and inputDict["function"] in MESSAGE_DICT:
            callback = MESSAGE_DICT[inputDict["function"]]["callback"]
            if "arg" in inputDict:
                output = callback(inputDict["arg"]) if callable(callback) else None
            else:
                output = callback() if callable(callback) else None
        if output is not None:
            await websocket.send(str(output))


async def main():
    print(f"Starting server on port {WEBSOCKET_PORT}")
    async with serve(socket_handler, None, WEBSOCKET_PORT):
        await asyncio.Future()  # run forever


asyncio.run(main())
