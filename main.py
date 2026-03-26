# Websocket example
import asyncio
from enum import Enum
from typing import Callable

from websockets.server import serve

from api import (
    line_follower_read,
    measure_distance,
    set_motor_speed,
    set_steering,
)


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
        message_type = int(message[0])
        output = None
        if message_type in MESSAGE_DICT:
            callback = MESSAGE_DICT[message_type]["callback"]
            output = callback(message[1:]) if callable(callback) else None
        if output is not None:
            await websocket.send(str(output))


async def main():
    async with serve(socket_handler, None, 8765):
        await asyncio.Future()  # run forever


asyncio.run(main())
