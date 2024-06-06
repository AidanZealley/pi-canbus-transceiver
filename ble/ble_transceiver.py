import dbus
import asyncio
from ble.advertisement import Advertisement
from ble.service import Application, Service, Characteristic, Descriptor
from canbus.handler import CANHandler

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 5000

class CountAdvertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("Count")
        self.include_tx_power = True

class CountService(Service):
    COUNT_SVC_UUID = "00000001-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, index, can_handler):
        self.can_handler = can_handler
        Service.__init__(self, index, self.COUNT_SVC_UUID, True)
        self.add_characteristic(CountCharacteristic(self))

class CountCharacteristic(Characteristic):
    COUNT_CHARACTERISTIC_UUID = "00000002-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, service):
        self.notifying = False
        Characteristic.__init__(self, self.COUNT_CHARACTERISTIC_UUID, ["notify", "read"], service)
        self.add_descriptor(CountDescriptor(self))

    def StartNotify(self):
        if self.notifying:
            return False
        
        self.notifying = True

        self.service.can_handler.add_subscriber(self)
        self.notify()

        return True

    async def StopNotify(self):
        if not self.notifying:
            return
        self.notifying = False
        await self.service.can_handler.remove_subscriber(self)

    async def notify(self, value):
        while self.notifying:
            count_value = str(value).encode()

            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": [dbus.Byte(c) for c in count_value]}, [])
            await asyncio.sleep(1)

    def ReadValue(self, options):
        value = str(self.service.can_handler.get_count()).encode()
        return [dbus.Byte(c) for c in value]

class CountDescriptor(Descriptor):
    COUNT_DESCRIPTOR_UUID = "2901"
    COUNT_DESCRIPTOR_VALUE = "Count Value"

    def __init__(self, characteristic):
        Descriptor.__init__(self, self.COUNT_DESCRIPTOR_UUID, ["read"], characteristic)

    def ReadValue(self, options):
        value = [dbus.Byte(c.encode()) for c in self.COUNT_DESCRIPTOR_VALUE]
        return value
    
async def main():
    can_handler = CANHandler()  # Initialize CAN handler
    app = Application()
    service = CountService(0, can_handler)
    app.add_service(service)
    app.register()

    adv = CountAdvertisement(0)
    adv.register()

    try:
        await asyncio.gather(
            app.run(),
            can_handler.receive_can_message()
        )
    except KeyboardInterrupt:
        app.quit()

if __name__ == "__main__":
    asyncio.run(main())