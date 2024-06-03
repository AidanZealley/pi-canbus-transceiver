from can_handler import CANHandler

def process_message(message):
    key, value = message
    print("Received message - Key:", hex(key), "Value:", value)
    can_handler.send_can_message(KEY, value)

if __name__ == "__main__":
    CAN_ID = 0x123
    MODULE_ID = 0x12
    KEY = 0x01

    can_handler = CANHandler(can_id=CAN_ID, module_id=MODULE_ID)
    can_handler.receive_can_message(process_message)
