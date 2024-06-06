from canbus.handler import CANHandler

class CANMessageSubscriber:
    def notify(self, count_value):
        print("Received message - Value:", count_value)

def main():
    CAN_ID = 0x123
    MODULE_ID = 0x12

    can_handler = CANHandler(can_id=CAN_ID, module_id=MODULE_ID)
    subscriber = CANMessageSubscriber()

    can_handler.add_subscriber(subscriber)
    can_handler.receive_can_message()

if __name__ == "__main__":
    main()
