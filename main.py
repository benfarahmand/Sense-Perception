import keyboard
import subprocess
import digitalio
import spidev as SPI
import ST7789
import time
import RPi.GPIO as GPIO
import time
import board
import busio
import adafruit_mlx90640
import math

from PIL import Image,ImageDraw,ImageFont

#thermal cam variables
MINTEMP = 10.0  # low range of the sensor (deg C)
MAXTEMP = 35.0  # high range of the sensor (deg C)
COLORDEPTH = 1000  # how many color values we can have
INTERPOLATE = 7 # 10  # scale factor for final image

i2c = busio.I2C(board.SCL, board.SDA, frequency=1000000) #800000)
mlx = adafruit_mlx90640.MLX90640(i2c)

mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_32_HZ

# the list of colors we can choose from
heatmap = (
    (0.0, (0, 0, 0)),
    (0.20, (0, 0, 0.5)),
    (0.40, (0, 0.5, 0)),
    (0.60, (0.5, 0, 0)),
    (0.80, (0.75, 0.75, 0)),
    (0.90, (1.0, 0.75, 0)),
    (1.00, (1.0, 1.0, 1.0)),
)

colormap = [0] * COLORDEPTH

# some utility functions
def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))


def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def gaussian(x, a, b, c, d=0):
    return a * math.exp(-((x - b) ** 2) / (2 * c ** 2)) + d

def gaussian(x, a, b, c, d=0):
    return a * math.exp(-((x - b) ** 2) / (2 * c ** 2)) + d


def gradient(x, width, cmap, spread=1):
    width = float(width)
    r = sum(
        [gaussian(x, p[1][0], p[0] * width, width / (spread * len(cmap))) for p in cmap]
    )
    g = sum(
        [gaussian(x, p[1][1], p[0] * width, width / (spread * len(cmap))) for p in cmap]
    )
    b = sum(
        [gaussian(x, p[1][2], p[0] * width, width / (spread * len(cmap))) for p in cmap]
    )
    r = int(constrain(r * 255, 0, 255))
    g = int(constrain(g * 255, 0, 255))
    b = int(constrain(b * 255, 0, 255))
    return r, g, b

for i in range(COLORDEPTH):
    colormap[i] = gradient(i, COLORDEPTH, heatmap)

# Raspberry Pi pin configuration:
RST = 27
DC = 25
BL = 18 #24
bus = 0 
device = 0 

# 240x240 display with hardware SPI:
disp = ST7789.ST7789(SPI.SpiDev(bus, device),RST, DC, BL)

# Initialize library.
disp.Init()

# lower the backlight
subprocess.call('gpio -g pwm 18 1024', shell=True)
subprocess.call('gpio -g mode 18 pwm', shell=True)
subprocess.call('gpio pwmc 1000',shell=True)
subprocess.call('gpio -g pwm 18 16',shell=True) #sets the  backlight from 0 - 1024

# Clear display and get ready to draw
disp.clear()

# Create images for drawing background and thermal camera output
background = Image.new("RGBA", (disp.width, disp.height), "BLACK")
thermalImg = Image.new("RGB", (32,24))
drawBackground = ImageDraw.Draw(background)
drawThermalImg = ImageDraw.Draw(thermalImg)
disp.ShowImage(background,0,0)

tImg_w = 32 * INTERPOLATE
tImg_h = 24 * INTERPOLATE
bg_w = 240
bg_h = 240
offsetX = int((bg_w - tImg_w)/2)
offsetY = int((bg_h - tImg_h)/2)

frame = [0] * 768
pixels = [0] * 768
while True:
        try:
                mlx.getFrame(frame)
#                time.sleep(0.0625)
        except (ValueError, RuntimeError) as e :
                print("ERROR")
                print(e)
                if e == 'Too many retries':
                        time.sleep(0.0625)
                continue

        for i, pixel in enumerate(frame):
                coloridx = map_value(pixel, MINTEMP, MAXTEMP, 0, COLORDEPTH - 1)
                coloridx = int(constrain(coloridx, 0, COLORDEPTH - 1))
                pixels[i] = colormap[coloridx]

        thermalImg.putdata(pixels)
        #        thermalImg = thermalImg.transpose(Image.FLIP_TOP_BOTTOM)
        thermalImgResized = thermalImg.resize((32 * INTERPOLATE, 24 * INTERPOLATE), Image.BICUBIC)

        #paste the thermal image to the background image
        background.paste(thermalImgResized,(offsetX,offsetY))

        disp.ShowImage(background,0,0)

        #font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf', 16)
        #draw.text((90, 70), ' ', fill = "BLUE" )
        #draw.text((90, 120), 'HELLO WORLD ', fill = "BLUE")

