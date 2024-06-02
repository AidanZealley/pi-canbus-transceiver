import can

can_interface = 'can0'
bus = can.interface.Bus(can_interface, bustype='socketcan', bitrate=100000)
can_ids = [
    0x0F6
]

def send_message(can_id, key, value):
    try:
        # Determine the number of bytes needed to represent the value
        can_dlc = 1  # Start with 1 byte for the key
        if value <= 0xFF:
            can_dlc += 1
        elif value <= 0xFFFF:
            can_dlc += 2
        elif value <= 0xFFFFFF:
            can_dlc += 3
        else:
            can_dlc += 4
        
        # Construct the data bytes for the CAN message
        data = bytearray()
        data.append(ord(key))  # Set the key in the first byte of data
        for i in range(can_dlc - 1):
            data.append((value >> (8 * i)) & 0xFF)  # Set the value in the following bytes
        
        # Create a CAN message object
        message = can.Message(arbitration_id=can_id, data=data)
        
        # Send the CAN message
        bus.send(message)
        
        print(f"Message sent with CAN ID: {can_id}, Key: {key}, Value: {value}")
        return True
    
    except can.CanError as e:
        print(f"Error: Failed to send CAN message. {e}")
        return False


def receive_can_message():
    try:
        while True:
            message = bus.recv()  # Wait until a message is received
            if message.arbitration_id in can_ids:
                key = chr(message.data[0])
                value = 0
                for i in range(1, message.dlc):
                    value |= message.data[i] << (8 * (i - 1))
                    print(f"Received - Key: {key}, Value: {value}")
                    send_message(can_ids[0], "B", 67890)

    except KeyboardInterrupt:
        print("Program interrupted")
    finally:
        print("Shutting down CAN bus")
        bus.shutdown()

if __name__ == "__main__":
    receive_can_message()
