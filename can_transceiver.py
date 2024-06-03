import can

can_interface = 'can0'
bus = can.interface.Bus(can_interface, bustype='socketcan', bitrate=100000)
can_ids = [
    0x123
]
can_modules = [
    0x12
]
keys = [
    0x01
]

def send_can_message(can_id, target_module, key, value):
    key_bytes = key.to_bytes(1, byteorder='big')
    value_bytes = value.to_bytes(4, byteorder='big')
    data = target_module.to_bytes(1, byteorder='big') + key_bytes + value_bytes
    message = can.Message(arbitration_id=can_id, data=data, is_extended_id=False)
    
    bus.send(message)

def read_can_message(message):
    can_id = message.arbitration_id
    data = message.data
    target_module = int.from_bytes(data[0:1], byteorder='big')
    key = int.from_bytes(data[1:2], byteorder='big')
    value = int.from_bytes(data[2:6], byteorder='big')
    
    return can_id, target_module, key, value


def receive_can_message():
    try:
        while True:
            message = bus.recv()
            if message.arbitration_id in can_ids:
                parsed_message = read_can_message(message)

                can_id = parsed_message.arbitration_id
                target_module = parsed_message.data[0]
                key = parsed_message.data[1]
                value_bytes = parsed_message.data[2:]
                value = int.from_bytes(value_bytes, byteorder='big')

                print("CAN ID:", hex(can_id))
                print("Target Module:", hex(target_module))
                print("Key:", hex(key))
                print("Value:", value)

                send_can_message(can_ids[0], can_modules[0], keys[0], 123)

    except KeyboardInterrupt:
        print("Program interrupted")
    finally:
        print("Shutting down CAN bus")
        bus.shutdown()

if __name__ == "__main__":
    receive_can_message()
