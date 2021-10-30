import keyboard
import subprocess
import digitalio
import pygame
import time
import RPi.GPIO as GPIO
import time
import board
import busio
import adafruit_mlx90640
import math
import os

from PIL import Image,ImageDraw,ImageFont

#thermal cam variables
MINTEMP = 20.0  # low range of the sensor (deg C)
MAXTEMP = 32.0  # high range of the sensor (deg C)
COLORDEPTH = 1000  # how many color values we can have
INTERPOLATE = 7 # 10  # scale factor for final image

i2c = busio.I2C(board.SCL, board.SDA, frequency=1000000)
mlx = adafruit_mlx90640.MLX90640(i2c)

mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_16_HZ

# init display
os.putenv('SDL_FBDEV', '/dev/fb0')
pygame.init()
window = pygame.display.set_mode((0,0),pygame.FULLSCREEN)
pygame.mouse.set_visible(False)

# the list of colors we can choose from
heatmap = (
    (0.00, (0,0,0)),
    (0.14, (0, 0, 1.0)),
    (0.28, (0.5,0,0.5)),
    (0.43, (0.3,0,0.51)),
    (0.57, (1.0, 0, 0)),
    (0.71, (1.0, 0.65, 0)),
    (0.86, (1.0,1.0,0)),
    (1.00, (1.0,1.0,1.0)),
)

colormap = [0] * COLORDEPTH

# some utility functions
def pilImageToSurface(pilImage):
    return pygame.image.fromstring(
        pilImage.tobytes(), pilImage.size, pilImage.mode).convert()

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

# lower the backlight
# subprocess.call('gpio -g pwm 18 1024', shell=True)
# subprocess.call('gpio -g mode 18 pwm', shell=True)
# subprocess.call('gpio pwmc 1000',shell=True)
# subprocess.call('gpio -g pwm 18 8',shell=True) #sets the  backlight from 0 - 1024

# Create images for drawing background and thermal camera output
background = Image.new("RGBA", (240, 240), "BLACK")
thermalImg = Image.new("RGB", (32,24))
drawBackground = ImageDraw.Draw(background)

tImg_w = 32 * INTERPOLATE
tImg_h = 24 * INTERPOLATE
bg_w = 240
bg_h = 240
offsetX = int((bg_w - tImg_w)/2)
offsetY = int((bg_h - tImg_h)/2)

frame = [0] * 768
frameMapped = [0] * 768
frameData = [0] * 834
pixels = [0] * 768
emissivity = 0.95
tr = 23.15
while True:
#       start_time = time.time() # for calculating Frames per Second
        try:
#                mlx.getFrame(frame) # regular way to get Frame from mlx adafruit library
                mlx._GetFrameData(frameData) 
                ta = mlx._GetTa(frameData) - 8
                mlx._CalculateTo(frameData,emissivity,tr,frame) #this function is slow. need to spend time reviewing the code to see if we can make it faster
                drawBackground.rectangle([(0,0),(240,240)],fill="BLACK")

#                for i in range(768):
#                        frameMapped[i]= int(map_value(frameData[i], 0, 65536,  COLORDEPTH - 1,$
#                        pixels[i] = colormap[frameMapped[i]]
#                print(frameData)
#                time.sleep(0.0625)
        except (ValueError, RuntimeError) as e :
                print("ERROR")
                print(e)
#                if e == 'Too many retries':
#                        time.sleep(0.0625)
                continue

        avgTemp = 0
        hiTemp = 0
        lowTemp = 1000
        for i, pixel in enumerate(frame):
                avgTemp=avgTemp+pixel
                if pixel > hiTemp:
                        hiTemp = pixel
                if pixel < lowTemp:
                        lowTemp = pixel
                coloridx = map_value(pixel, MINTEMP, MAXTEMP, 0, COLORDEPTH - 1)
                coloridx = int(constrain(coloridx, 0, COLORDEPTH - 1))
                pixels[i] = colormap[coloridx]
                avgTemp = avgTemp/768
        MINTEMP = avgTemp - 5
        MAXTEMP = avgTemp + 5
        avgTemp = int(1.8*(avgTemp)+32)
        hiTemp = int(1.8*(hiTemp)+32)
        lowTemp = int(1.8*(lowTemp)+32)

        thermalImg.putdata(pixels)
        thermalImg = thermalImg.transpose(Image.FLIP_LEFT_RIGHT) #FLIP_TOP_BOTTOM)
        thermalImgResized = thermalImg.resize((32 * INTERPOLATE, 24 * INTERPOLATE), Image.BICUBIC)

        #paste the thermal image to the background image
        background.paste(thermalImgResized,(offsetX,offsetY))
        drawBackground.text((5,210),"High Temp: "+str(hiTemp) + "F",fill="WHITE")
        drawBackground.text((120,210),"Low Temp: "+str(lowTemp) + "F",fill="WHITE")
        drawBackground.text((5,220),"Avg. Temp: "+str(avgTemp) + "F",fill="WHITE")

        pygameSurface = pilImageToSurface(background)
        window.blit(pygameSurface, pygameSurface.get_rect(center = (120, 120)))
        pygame.display.update()

