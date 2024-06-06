import can
import asyncio

class CANHandler:
    def __init__(self, interface='can0', bitrate=100000, can_id=None, module_id=None):
        self.bus = can.interface.Bus(interface, bustype='socketcan', bitrate=bitrate)
        self.can_id = can_id
        self.module_id = module_id

        if can_id is not None or module_id is not None:
            self.set_filters(can_id, module_id)

    def set_filters(self, can_id=None, module_id=None):
        filters = []

        if can_id is not None:
            filters.append({"can_id": can_id, "can_mask": 0x7FF, "extended": False})

        if module_id is not None:
            # Assuming module_id is part of the CAN data payload and requires additional handling
            # You could add more complex filtering here if needed
            
            # Example: filter on first byte of data payload being the module_id
            # This is a simplistic filter assuming you can set data payload filters directly
            filters.append({"can_id": 0, "can_mask": 0, "extended": False, "data": [module_id]})

        self.bus.set_filters(filters)

    async def send_can_message(self, key, value):
        key_bytes = key.to_bytes(1, byteorder='big')
        value_bytes = value.to_bytes(4, byteorder='big')
        data = self.module_id.to_bytes(1, byteorder='big') + key_bytes + value_bytes
        message = can.Message(arbitration_id=self.can_id, data=data, is_extended_id=False)
        
        self.bus.send(message)

    def read_can_message(self, message):
        can_id = message.arbitration_id
        data = message.data
        target_module = int.from_bytes(data[0:1], byteorder='big')
        key = int.from_bytes(data[1:2], byteorder='big')
        value = int.from_bytes(data[2:6], byteorder='big')
        
        return can_id, target_module, key, value

    async def receive_can_message(self, callback):
        loop = asyncio.get_event_loop()
        while True:
            message = await loop.run_in_executor(None, self.bus.recv)
            can_id, target_module, key, value = self.read_can_message(message)

            print("CAN ID:", hex(can_id))
            print("Target Module:", hex(target_module))
            print("Key:", hex(key))
            print("Value:", value)

            response = (key, value)

            await callback(response)
