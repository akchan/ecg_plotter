#!/usr/bin/env python
# coding: UTF-8


'''
Usage
=====

ssh pi@raspberrypi.local '/home/pi/.pyenv/shims/python -u [path to this script]'

* Use `-u` option to disable the buffer

'''

import time
from collections import deque

# Usage of luma.oled 
# https://luma-oled.readthedocs.io/en/latest/python-usage.html
from luma.core.interface.serial import i2c, spi
from luma.core.render import canvas
from luma.oled.device import ssd1306

from PIL import ImageFont

import Adafruit_ADS1x15


VERSION = '2019-04-20'


class OledDisplay:
    '''
    Used libray : luma.OLED
      See https://luma-oled.readthedocs.io/en/latest/

    Memo
    ----
    system font => '/usr/share/fonts/truetype/freefont/FreeSans.ttf'
    '''
    def __init__(self, width=128, height=64,
                black_band_ratio=0.1, min_window_width=50,
                font_path='/home/pi/dev/190408_ecg/ecg_ssh/mplus_f12b.bdf', font_size=12,
                spacing=14,
                debug=False):
        self.width       = width
        self.height      = height
        self.device      = self.__init_ssd1306(height=height)
        self.len_lim     = round(self.device.width * (1 - black_band_ratio))
        self.min_window_width = min_window_width
        self.font        = ImageFont.truetype(font_path, font_size)
        self.spacing     = spacing
        self.debug       = debug

        self.clear()


    def __init_ssd1306(self, height):
        '''
        Memo
        ====

        Use device=0 when connecting CS of display to P01-24 (GPIO 8 [CE0]).
        '''
        serial = spi(device=0, port=0)
        device = ssd1306(serial, width=self.width, height=height)
        return device


    def clear(self):
        self.vals = deque(maxlen=self.len_lim)
        self.i    = -1

        with canvas(self.device) as draw:
            pass


    def add_val(self, val):
        self.i = (self.i + 1) % self.device.width
        self.vals.append(val)


    def draw(self):
        lines = self.__val_lines()

        with canvas(self.device) as draw:
            latest_val = self.vals[-1]
            draw.text((0, 0), 'Value: {:5.0f}'.format(latest_val), fill='white', font=self.font)

            for line in lines:
                draw.line(line, fill="white", width=1)


    def show_shutdown(self):
        # self.to_height64()
        with canvas(self.device) as draw:
            draw.text((0, 0), 'Shutdown...', fill='white', font=self.font)


    def show_text(self, text):
        with canvas(self.device) as draw:
            draw.multiline_text((0, 0), text, fill='white', spacing=self.spacing, align='left', font=self.font)


    def to_height32(self):
        if 64 == self.height:
            self.device = self.__init_ssd1306(height=32)
            self.height = 32


    def to_height64(self):
        if 32 == self.height:
            self.device = self.__init_ssd1306(height=64)
            self.height = 64


    def __normalized_vals(self, vals, device_height, min_window_width):
        val_max = max(vals)
        val_min = min(vals)
        val_diff = val_max - val_min

        val_diff = max(val_diff, min_window_width)

        normalized_vals = [(device_height - 1) * (1 - (p - val_min) / (val_diff)) for p in vals]

        return normalized_vals


    def __val_lines(self):
        p = self.__normalized_vals(self.vals, self.device.height, self.min_window_width)
        l = len(p)
        lines = []

        if l > self.i + 1:
            line_l_x = list(range(0, self.i + 1))
            line_l_y = p[(l - (self.i + 1)):l]
            lines.append(list(zip(line_l_x, line_l_y)))

            n_rest = l - (self.i + 1)

            line_r_x = list(range(self.device.width - n_rest, self.device.width))
            line_r_y = p[0:n_rest]
            lines.append(list(zip(line_r_x, line_r_y)))

            # embed()
        else:
            i_end   = self.i + 1
            i_start = i_end - l

            line_x = list(range(i_start, i_end))
            line_y = p
            lines.append(list(zip(line_x, line_y)))

        return lines


def main(spf=0.01):
    adc = Adafruit_ADS1x15.ADS1015()

    # Use one of these data rate: 128 ,250, 490, 920, 1600
    adc.start_adc(0, gain=1, data_rate=128)

    oled = OledDisplay()
    oled.show_text('Monitoring ECG...')

    t = time.time()

    while True:
        val = adc.get_last_result()

        print(val)

        t += spf
        t_tmp = time.time()
        t_rest = t - t_tmp
        if t_rest > 0:
            time.sleep(t_rest)
        elif abs(t_rest) > 5:
            print('Internal timer error!')
            break


if __name__ == '__main__':
    main()
