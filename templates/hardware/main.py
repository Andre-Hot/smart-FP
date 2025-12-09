import network
import time
import urequests
import ujson
from machine import Pin, ADC, I2C

SSID = ""
PASSWORD = ""
SERVER_URL = ""
BORGER_ID = 3

#Pulsmåler 
puls_sensor = ADC(Pin(34))
puls_sensor.atten(ADC.ATTN_11DB)

#Batteri
batteri_sensor = ADC(Pin(35))
batteri_sensor.atten(ADC.ATTN_11DB)

#MPU6050 Falddetektor
i2c = I2C(0, scl=Pin(22), sda=Pin(21))

#MPU6050 driver
class MPU6050:
    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr
        # Væk sensoren
        try:
            self.i2c.writeto_mem(self.addr, 0x6B, b'\x00')
        except:
            print("Kunne ikke kontakte MPU6050")
        
    def get_accel(self):
        try:
            data = self.i2c.readfrom_mem(self.addr, 0x3B, 6)
            x = self.bytes_to_int(data[0], data[1])
            y = self.bytes_to_int(data[2], data[3])
            z = self.bytes_to_int(data[4], data[5])
            return x, y, z
        except:
            return 0, 0, 0

    def bytes_to_int(self, msb, lsb):
        val = (msb << 8) | lsb
        if val & 0x8000: return val - 65536
        return val
    
# Start sensoren
try:
    mpu = MPU6050(i2c)
    print("MPU6050 sensor klar!")
except:
    print("FEJL: Tjek ledninger til MPU6050 (SDA=21, SCL=22)")
    mpu = None

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Forbinder til WiFi...')
        wlan.connect(SSID, PASSWORD)
        retry = 0
        while not wlan.isconnected() and retry < 20:
            time.sleep(1)
            print('.', end='')
            retry += 1
            
    if wlan.isconnected():
        print('\nWiFi forbundet:', wlan.ifconfig())
    else:
        print('\nKunne ikke forbinde. Tjek SSID/Password.')
