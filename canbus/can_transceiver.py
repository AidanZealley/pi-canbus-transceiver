from canbus.handler import CANHandler

class CANMessageSubscriber:
    def __init__(self, can_handler):
        self.can_handler = can_handler

    def notify(self, count_value):
        print("Received message - Value:", count_value)
        self.can_handler.send_can_message(0x01, count_value)

def main():
    CAN_ID = 0x123
    MODULE_ID = 0x12

    can_handler = CANHandler(can_id=CAN_ID, module_id=MODULE_ID)
    subscriber = CANMessageSubscriber(can_handler)

    can_handler.add_subscriber(subscriber)
    can_handler.receive_can_message()

if __name__ == "__main__":
    main()
