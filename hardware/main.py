import network
import time
import urequests
import ujson
from machine import Pin, ADC, I2C, PWM

SSID = ""
PASSWORD = ""
SERVER_URL = ""
BORGER_ID = 3

Puls_min = 50
Puls_max = 120

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

def laes_puls():
    raw_value = puls_sensor.read()
    puls_bpm = int((raw_value / 4095) * 150) + 40
    if puls_bpm < 45: puls_bpm = 0 # Filtrer støj hvis sensoren ikke er på
    return puls_bpm

def tjek_fald():
    if mpu is None: return False
    x, y, z = mpu.get_accel()
    
   # Beregn G-kraft (16384 er 1G for denne sensor)
    g_force = (abs(x) + abs(y) + abs(z)) / 16384.0
    
    # Hvis kraften er over 2.5G, registrerer vi et fald
    if g_force > 2.5:
        return True
    return False

def laes_batteri():
    raw = batteri_sensor.read()
    # Omregn til procent (3.0V = 0%, 4.2V = 100%)
    volt = (raw / 4095) * 3.3 * 2 # Gang med 2 pga spændingsdeler
    procent = int((volt - 3.0) / (4.2 - 3.0) * 100)
    return max(0, min(100, procent))

# --- 4. HOVED PROGRAM ---

print("Starter Smart Vest...")
connect_wifi()

print(f"Måler data for Borger ID {BORGER_ID}...")

while True:
    try:
        # Læs sensorer
        puls = laes_puls()
        fald = tjek_fald()
        batteri = laes_batteri()
        
        if fald:
            print("!!! FALD DETEKTERET !!!")

        # Pak data
        payload = {
            "borger_id": BORGER_ID,
            "puls": puls,
            "fald": fald
        }
        
        print(f"Batt: {batteri}% - Sender: {payload}")

        # Send til server
        headers = {'Content-Type': 'application/json'}
        res = urequests.post(SERVER_URL, data=ujson.dumps(payload), headers=headers)
        res.close() # Luk forbindelse for at spare hukommelse
        
    except OSError:
        print("Netværksfejl (Tjek Hotspot og IP)")
        try: connect_wifi() 
        except: pass
    except Exception as e:
        print("Fejl:", e)

    time.sleep(1) # Opdater hvert sekund