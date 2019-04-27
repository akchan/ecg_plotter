#!/usr/bin/env python
# coding: UTF-8

import time

def main():
    t = time.time()
    while True:
        t_new = time.time()
        t_frame = t_new - t
        t = t_new
        print('test {:3.1f} ms'.format(t_frame))


if __name__ == '__main__':
    main()
