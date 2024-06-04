#!/usr/bin/python3

import dbus
import can

from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor

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

    def receive_can_message(self, callback=None):
        while True:
            message = self.bus.recv()
            can_id, target_module, key, value = self.read_can_message(message)

            print("CAN ID:", hex(can_id))
            print("Target Module:", hex(target_module))
            print("Key:", hex(key))
            print("Value:", value)

            response = (key, value)

            if callback is not None:
                callback(response)

            return response

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 5000

CAN_ID = 0x123
MODULE_ID = 0x12

can_handler = CANHandler(can_id=CAN_ID, module_id=MODULE_ID)

class ThermometerAdvertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("Thermometer")
        self.include_tx_power = True

class ThermometerService(Service):
    THERMOMETER_SVC_UUID = "00000001-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, index):
        self.farenheit = True

        Service.__init__(self, index, self.THERMOMETER_SVC_UUID, True)
        self.add_characteristic(TempCharacteristic(self))
        self.add_characteristic(UnitCharacteristic(self))

    def is_farenheit(self):
        return self.farenheit

    def set_farenheit(self, farenheit):
        self.farenheit = farenheit

class TempCharacteristic(Characteristic):
    TEMP_CHARACTERISTIC_UUID = "00000002-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, service):
        self.notifying = False

        Characteristic.__init__(
                self, self.TEMP_CHARACTERISTIC_UUID,
                ["notify", "read"], service)
        self.add_descriptor(TempDescriptor(self))

    def get_temperature(self):
        value = []
        unit = "C"

        _, value = can_handler.receive_can_message()

        temp = value
        if self.service.is_farenheit():
            unit = "F"

        strtemp = str(round(temp, 1)) + " " + unit
        for c in strtemp:
            value.append(dbus.Byte(c.encode()))

        return value

    def set_temperature_callback(self):
        if self.notifying:
            value = self.get_temperature()
            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])

        return self.notifying

    def StartNotify(self):
        if self.notifying:
            return

        self.notifying = True

        value = self.get_temperature()
        self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        self.add_timeout(NOTIFY_TIMEOUT, self.set_temperature_callback)

    def StopNotify(self):
        self.notifying = False

    def ReadValue(self, options):
        value = self.get_temperature()

        return value

class TempDescriptor(Descriptor):
    TEMP_DESCRIPTOR_UUID = "2901"
    TEMP_DESCRIPTOR_VALUE = "CPU Temperature"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.TEMP_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.TEMP_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value

class UnitCharacteristic(Characteristic):
    UNIT_CHARACTERISTIC_UUID = "00000003-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, service):
        Characteristic.__init__(
                self, self.UNIT_CHARACTERISTIC_UUID,
                ["read", "write"], service)
        self.add_descriptor(UnitDescriptor(self))

    def WriteValue(self, value, options):
        val = str(value[0]).upper()
        if val == "C":
            self.service.set_farenheit(False)
        elif val == "F":
            self.service.set_farenheit(True)

    def ReadValue(self, options):
        value = []

        if self.service.is_farenheit(): val = "F"
        else: val = "C"
        value.append(dbus.Byte(val.encode()))

        return value

class UnitDescriptor(Descriptor):
    UNIT_DESCRIPTOR_UUID = "2901"
    UNIT_DESCRIPTOR_VALUE = "Temperature Units (F or C)"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.UNIT_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.UNIT_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value

app = Application()
app.add_service(ThermometerService(0))
app.register()

adv = ThermometerAdvertisement(0)
adv.register()

try:
    app.run()
except KeyboardInterrupt:
    app.quit()
