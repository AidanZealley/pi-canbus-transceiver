from dasbus.connection import SessionMessageBus
from dasbus.server.interface import DBusInterface, dbus_method, dbus_signal
from dasbus.server.publishable import Publishable
from bletools import BleTools

BLUEZ_SERVICE_NAME = "org.bluez"
GATT_MANAGER_IFACE = "org.bluez.GattManager1"
DBUS_OM_IFACE = "org.freedesktop.DBus.ObjectManager"
DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"
GATT_SERVICE_IFACE = "org.bluez.GattService1"
GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
GATT_DESC_IFACE = "org.bluez.GattDescriptor1"

class Application(Publishable):
    def __init__(self):
        self.bus = BleTools.get_bus()
        self.path = "/"
        self.services = []
        self.next_index = 0

    @dbus_method(DBUS_OM_IFACE, out_signature="a{oa{sa{sv}}}")
    def GetManagedObjects(self):
        response = {}

        for service in self.services:
            response[service.get_path()] = service.get_properties()
            for chrc in service.get_characteristics():
                response[chrc.get_path()] = chrc.get_properties()
                for desc in chrc.get_descriptors():
                    response[desc.get_path()] = desc.get_properties()

        return response

    def register_app_callback(self):
        print("GATT application registered")

    def register_app_error_callback(self, error):
        print(f"Failed to register application: {error}")

    def register(self):
        adapter = BleTools.find_adapter(self.bus)
        service_manager = self.bus.get_proxy(BLUEZ_SERVICE_NAME, adapter)
        service_manager.RegisterApplication(self.path, {},
                                            self.register_app_callback,
                                            self.register_app_error_callback)

class Service(Publishable):
    PATH_BASE = "/org/bluez/example/service"

    def __init__(self, index, uuid, primary):
        self.bus = BleTools.get_bus()
        self.path = f"{self.PATH_BASE}{index}"
        self.uuid = uuid
        self.primary = primary
        self.characteristics = []

    @dbus_method(DBUS_PROP_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        if interface != GATT_SERVICE_IFACE:
            raise InvalidArgsException()
        return self.get_properties()[GATT_SERVICE_IFACE]

    def get_properties(self):
        return {
            GATT_SERVICE_IFACE: {
                "UUID": self.uuid,
                "Primary": self.primary,
                "Characteristics": [chrc.get_path() for chrc in self.characteristics]
            }
        }

    def add_characteristic(self, characteristic):
        self.characteristics.append(characteristic)

    def get_characteristics(self):
        return self.characteristics

class Characteristic(Publishable):
    def __init__(self, uuid, flags, service):
        index = service.get_next_index()
        self.path = f"{service.path}/char{index}"
        self.bus = service.get_bus()
        self.uuid = uuid
        self.service = service
        self.flags = flags
        self.descriptors = []

    @dbus_method(DBUS_PROP_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        if interface != GATT_CHRC_IFACE:
            raise InvalidArgsException()
        return self.get_properties()[GATT_CHRC_IFACE]

    @dbus_method(GATT_CHRC_IFACE, in_signature="a{sv}", out_signature="ay")
    def ReadValue(self, options):
        print("Default ReadValue called, returning error")
        raise NotSupportedException()

    @dbus_method(GATT_CHRC_IFACE, in_signature="aya{sv}")
    def WriteValue(self, value, options):
        print("Default WriteValue called, returning error")
        raise NotSupportedException()

    @dbus_method(GATT_CHRC_IFACE)
    def StartNotify(self):
        print("Default StartNotify called, returning error")
        raise NotSupportedException()

    @dbus_method(GATT_CHRC_IFACE)
    def StopNotify(self):
        print("Default StopNotify called, returning error")
        raise NotSupportedException()

    def get_properties(self):
        return {
            GATT_CHRC_IFACE: {
                "Service": self.service.get_path(),
                "UUID": self.uuid,
                "Flags": self.flags,
                "Descriptors": [desc.get_path() for desc in self.descriptors]
            }
        }

    def add_descriptor(self, descriptor):
        self.descriptors.append(descriptor)

    def get_descriptors(self):
        return self.descriptors

class Descriptor(Publishable):
    def __init__(self, uuid, flags, characteristic):
        index = characteristic.get_next_index()
        self.path = f"{characteristic.path}/desc{index}"
        self.uuid = uuid
        self.flags = flags
        self.chrc = characteristic
        self.bus = characteristic.get_bus()

    @dbus_method(DBUS_PROP_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        if interface != GATT_DESC_IFACE:
            raise InvalidArgsException()
        return self.get_properties()[GATT_DESC_IFACE]

    @dbus_method(GATT_DESC_IFACE, in_signature="a{sv}", out_signature="ay")
    def ReadValue(self, options):
        print("Default ReadValue called, returning error")
        raise NotSupportedException()

    @dbus_method(GATT_DESC_IFACE, in_signature="aya{sv}")
    def WriteValue(self, value, options):
        print("Default WriteValue called, returning error")
        raise NotSupportedException()

    def get_properties(self):
        return {
            GATT_DESC_IFACE: {
                "Characteristic": self.chrc.get_path(),
                "UUID": self.uuid,
                "Flags": self.flags
            }
        }

class CharacteristicUserDescriptionDescriptor(Descriptor):
    CUD_UUID = "2901"

    def __init__(self, uuid, flags, characteristic):
        super().__init__(uuid, flags, characteristic)
        self.writable = "writable-auxiliaries" in characteristic.flags
        self.value = bytearray(b"This is a characteristic for testing").tolist()

    def ReadValue(self, options):
        return self.value

    def WriteValue(self, value, options):
        if not self.writable:
            raise NotPermittedException()
        self.value = value
