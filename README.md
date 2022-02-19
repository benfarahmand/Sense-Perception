# Sense-Perception

A project to allow me to perceive the world through technologically enhanced senses via a wearable HUD.


### Hardware:
- Raspberry Pi Zero WH
- MLX90640 IR Thermal Camera: https://cdn-learn.adafruit.com/downloads/pdf/adafruit-mlx90640-ir-thermal-camera.pdf
- 1.3 Inch 240x240 ST7789 LCD by Waveshare: https://www.waveshare.com/w/upload/7/70/1.3inch_LCD_Module_user_manual_en.pdf


### Other Libraries Used:
- For LCD using https://github.com/juj/fbcp-ili9341
- For MLX90640 IR Thermal Camera: https://github.com/adafruit/Adafruit_CircuitPython_MLX90640/

### Starting Raspberry Pi Zero WH without Keyboard or Mouse:
- Followed the instructions here: https://forums.raspberrypi.com/viewtopic.php?p=1264992&sid=5cbbe41097e5ec17f974dc34f06beaa5#p1264992
- Made the wpa_supplicant.conf file in the boot section of the RPi OS Image in the SD card with structure shown below:
```
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=US
network={
     ssid="Your network name/SSID"
     psk="Your WPA/WPA2 security key"
     key_mgmt=WPA-PSK
}
```

### Setting up 1.3 inch 240x240 pixel LCD with fbcp-ili9341:

- was able to get ST7789 working with fbcp-ili9341 library with following cmake options:
cmake -DST7789=ON -DGPIO_TFT_DATA_CONTROL=25 -DGPIO_TFT_RESET_PIN=27 -DGPIO_TFT_BACKLIGHT=18 -DSPI_BUS_CLOCK_DIVISOR=10 -DSTATISTICS=0 -DUSE_DMA_TRANSFERS=OFF ..

- Used the following settings in raspberry pi config file:
- Go to boot/config.txt then use these settings for no HDMI display and instead using the ST7789
```
hdmi_group=2
hdmi_mode=87
hdmi_cvt=240 240 60 1 0 0 0
hdmi_force_hotplug=1
display_rotate=1
```
