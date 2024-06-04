from dasbus.connection import SessionMessageBus
from dasbus.server.interface import DBusInterface, dbus_method
from bletools import BleTools

BLUEZ_SERVICE_NAME = "org.bluez"
LE_ADVERTISING_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"
DBUS_OM_IFACE = "org.freedesktop.DBus.ObjectManager"
DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"
LE_ADVERTISEMENT_IFACE = "org.bluez.LEAdvertisement1"

class Advertisement(Publishable):
    PATH_BASE = "/org/bluez/example/advertisement"

    def __init__(self, index, advertising_type):
        self.path = f"{self.PATH_BASE}{index}"
        self.bus = BleTools.get_bus()
        self.ad_type = advertising_type
        self.local_name = None
        self.service_uuids = None
        self.solicit_uuids = None
        self.manufacturer_data = None
        self.service_data = None
        self.include_tx_power = None

    @dbus_method(DBUS_PROP_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        if interface != LE_ADVERTISEMENT_IFACE:
            raise InvalidArgsException()
        return self.get_properties()[LE_ADVERTISEMENT_IFACE]

    @dbus_method(LE_ADVERTISEMENT_IFACE, in_signature="", out_signature="")
    def Release(self):
        print(f"{self.path}: Released!")

    def get_properties(self):
        properties = {"Type": self.ad_type}

        if self.local_name is not None:
            properties["LocalName"] = self.local_name

        if self.service_uuids is not None:
            properties["ServiceUUIDs"] = self.service_uuids

        if self.solicit_uuids is not None:
            properties["SolicitUUIDs"] = self.solicit_uuids

        if self.manufacturer_data is not None:
            properties["ManufacturerData"] = self.manufacturer_data

        if self.service_data is not None:
            properties["ServiceData"] = self.service_data

        if self.include_tx_power is not None:
            properties["IncludeTxPower"] = self.include_tx_power

        return {LE_ADVERTISEMENT_IFACE: properties}

    def add_service_uuid(self, uuid):
        if not self.service_uuids:
            self.service_uuids = []
        self.service_uuids.append(uuid)

    def add_solicit_uuid(self, uuid):
        if not self.solicit_uuids:
            self.solicit_uuids = []
        self.solicit_uuids.append(uuid)

    def add_manufacturer_data(self, manuf_code, data):
        if not self.manufacturer_data:
            self.manufacturer_data = {}
        self.manufacturer_data[manuf_code] = data

    def add_service_data(self, uuid, data):
        if not self.service_data:
            self.service_data = {}
        self.service_data[uuid] = data

    def add_local_name(self, name):
        self.local_name = name

    def register_ad_callback(self):
        print("GATT advertisement registered")

    def register_ad_error_callback(self, error):
        print(f"Failed to register GATT advertisement: {error}")

    def register(self):
        adapter = BleTools.find_adapter(self.bus)
        ad_manager = self.bus.get_proxy(BLUEZ_SERVICE_NAME, adapter)
        ad_manager.RegisterAdvertisement(self.path, {},
                                         self.register_ad_callback,
                                         self.register_ad_error_callback)
