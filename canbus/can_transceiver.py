import asyncio
from canbus.handler import CANHandler

class CANMessageSubscriber:
    async def notify(self, count_value):
        print("Received message - Value:", count_value)

async def main():
    CAN_ID = 0x123
    MODULE_ID = 0x12

    can_handler = CANHandler(can_id=CAN_ID, module_id=MODULE_ID)
    subscriber = CANMessageSubscriber()
    can_handler.add_subscriber(subscriber)

    await can_handler.receive_can_message()

if __name__ == "__main__":
    asyncio.run(main())
