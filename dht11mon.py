#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  1 17:22:55 2022

@author: phykc
"""
import RPi.GPIO as GPIO
import dht11
import time

# initialize GPIO
class Temphum:
    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.cleanup()
    def read(self):
        # read data using pin 14
        instance = dht11.DHT11(pin = 14)
        result = instance.read()
        attempts=0
        while not result.is_valid() and attempts<5:
            time.sleep(3)
            result = instance.read()
            attempts+1
        if result.is_valid(): 
            print("Ambient Temperature: %-3.1f C" % result.temperature)
            print("Humidity: %-3.1f %%" % result.humidity)
            return result.temperature, result.humidity
        else:
            print("Error: %d" % result.error_code)
            return 25,45

        

