import asyncio
from canbus.handler import CANHandler

async def process_message(message):
    key, value = message
    print("Received message - Key:", hex(key), "Value:", value)

async def main():
    CAN_ID = 0x123
    MODULE_ID = 0x12

    can_handler = CANHandler(can_id=CAN_ID, module_id=MODULE_ID)
    await can_handler.receive_can_message(process_message)

if __name__ == "__main__":
    asyncio.run(main())
