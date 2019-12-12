import adbutils
import time


class WXadb(object):
    adb = adbutils.AdbClient(host="127.0.0.1", port=5037)
    devices = {}

    def add_device(self, d_serial):
        d = self.adb.device(serial=d_serial)
        self.devices[d_serial] = d

    def send_WX_msg(self, msg):
        for s, d in self.devices.items():
            d.keyevent("HOME")
            d.swipe(300, 1800, 300, 800, 0.5)
            d.shell("am start -n com.tencent.mm/com.tencent.mm.ui.LauncherUI")
            time.sleep(1)
            d.click(313, 1841)
            d.send_keys(msg)
            d.click(967, 1788)
