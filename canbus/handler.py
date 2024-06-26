import can
import asyncio

NOTIFY_TIMEOUT = 1000

class CANHandler:
    def __init__(self, interface='can0', bitrate=100000, can_id=None, module_id=None):
        self.bus = can.interface.Bus(interface, bustype='socketcan', bitrate=bitrate)
        self.can_id = can_id
        self.module_id = module_id
        self.subscribers = set()
        self._stop_flag = False

        if can_id is not None or module_id is not None:
            self.set_filters(can_id, module_id)

    def set_filters(self, can_id=None, module_id=None):
        filters = []

        if can_id is not None:
            filters.append({"can_id": can_id, "can_mask": 0x7FF, "extended": False})

        if module_id is not None:
            filters.append({"can_id": 0, "can_mask": 0, "extended": False, "data": [module_id]})

        self.bus.set_filters(filters)

    def send_can_message(self, key, value):
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

    async def receive_can_message(self):
        print("Starting CAN message receiving loop.")
        while True:
            try:
                # Run the blocking recv call in a separate thread
                message = await asyncio.to_thread(self.bus.recv, timeout=1)
                if message:
                    can_id, target_module, key, value = self.read_can_message(message)
                    print(f"Received CAN message: can_id={can_id}, target_module={target_module}, key={key}, value={value}")
                    for subscriber in self.subscribers:
                        asyncio.create_task(subscriber.notify(value))
                else:
                    print("No CAN message received within timeout period.")
            except Exception as e:
                print(f"Error receiving CAN message: {e}")

    def add_subscriber(self, subscriber):
        # start
        print("New subscriber")
        self.subscribers.add(subscriber)

    def remove_subscriber(self, subscriber):
        # stop if sub list empty
        self.subscribers.remove(subscriber)

    def stop(self):
        self._stop_flag = True