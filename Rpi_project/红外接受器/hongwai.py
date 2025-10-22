from evdev import InputDevice, list_devices, categorize, ecodes
#https://python-evdev.readthedocs.io/en/latest/tutorial.html#listing-accessible-event-devices
#https://s761111.gitbook.io/raspi-sensor/shu-mei-pai-yu-gong-wai-xian#si-kong-zhi-vlc-bo-fang-yin-lao-ji-led-shan-shuo
def get_ir_device():
    devices = [InputDevice(path) for path in list_devices()]
    for device in devices:
        print(device.path, device.name, device.phys)
        if 'ir_recv' in device.name:
            return device
        else:
            device.close()

dev = get_ir_device()
try:
    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY:
            if event.value == 1:
                if ecodes.KEY[event.code] == 'KEY_1':
                    print('press 1')
                elif ecodes.KEY[event.code] == 'KEY_2':
                    print('press 2')
                elif ecodes.KEY[event.code] == 'KEY_3':
                    print('press 3')
                    dev.close()
                    quit()
except KeyboardInterrupt:
    print('press ctrl-c')
    dev.close()
    quit()