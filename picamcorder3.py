#!/usr/bin/env python2.7
# script by Alex Eames http://RasPi.tv
# Updated version for use with Adafruit PiTFT & fbcp
# needs RPi.GPIO 0.5.2 or later
# also needs fbcp from https://github.com/tasanakorn/rpi-fbcp
# needs /home/pi/RasPiCamcorder/raspitv320x240.jpg
# and imagemagick
# set up PiTFT as at 
# http://learn.adafruit.com/adafruit-pitft-28-inch-resistive-touchscreen-display-raspberry-pi/
# but WITHOUT enabling/allocating a button to the power on/off feature
# No guarantees. No responsibility accepted. It works for me.
# If you need help with it, sorry I haven't got time. I'll try and add more
# documentation as time goes by. But no promises.

import RPi.GPIO as GPIO
from subprocess import call
import subprocess
from time import sleep
import time
import sys
import os
import pygame

os.environ["SDL_FBDEV"] = "/dev/fb1"
screen = 1
still = 0
start_fbcp = '/home/pi/RasPiCamcorderPiTFT/fbcp &'
kill_fbcp = 'pkill fbcp'

if GPIO.RPI_REVISION == 1:
    screen_port = 21
else:
    screen_port = 27

# define four commands for control of PiTFT backlight
cmd = 'sudo sh -c "echo 252 > /sys/class/gpio/export"'  # set up link to TFT controller
call ([cmd], shell=True)
cmd = 'sudo sh -c "echo \'out\' > /sys/class/gpio/gpio252/direction"' # set as output
call ([cmd], shell=True)
cmd_on = 'sudo sh -c "echo \'1\' > /sys/class/gpio/gpio252/value"' # TFT on
call ([cmd_on], shell=True)
# define cmd_off, but don't use it at this stage - we want it on for now
cmd_off = 'sudo sh -c "echo \'0\' > /sys/class/gpio/gpio252/value"' # TFT off

front_led_status = sys.argv[-1]
if front_led_status == "0":
    print "front LED off"
    front_led_status = 0

GPIO.setmode(GPIO.BCM)

# GPIO 23 RECORD button set up as input, pulled up to avoid false detection.
# All ports are wired to connect to GND on button press.
# So we'll be setting up falling edge detection and using built-in pull-ups
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# GPIO 22 STOP, CLOSE & Shutdown input, pulled up, connected to GND on button press 
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# GPIO 21/27 toggle TFT screen
GPIO.setup(screen_port, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# GPIO 18 for stills
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Set up GPIO 5 for camera LED control
GPIO.setup(5, GPIO.OUT)

recording = 0
vid_rec_num = "vid_rec_num.txt"   
vid_rec_num_fp ="/home/pi/RasPiCamcorderPiTFT/vid_rec_num.txt" # need full path if run from rc.local
photo_rec_num ="photo_rec_num.txt" 
photo_rec_num_fp ="/home/pi/RasPiCamcorderPiTFT/photo_rec_num.txt" # need full path if run from rc.local
base_vidfile = "raspivid -t 3600000 -o /home/pi/video"
time_off = time.time()

def write_rec_num(options):
    if options == 1:
        vrnw = open(vid_rec_num_fp, 'w')
        vrnw.write(str(rec_num))
        vrnw.close()
    if options == 2:
        prnw = open(photo_rec_num_fp, 'w')
        prnw.write(str(photo_num))
        prnw.close()

def toggle_screen(channel):
    global screen
    screen += 1
    if (recording == 0 and screen % 2 == 0):
        call ([cmd_off], shell=True)
    else:
        call ([cmd_on], shell=True)

def start_recording(rec_num):
    global recording
    if recording == 0:
        call ([start_fbcp], shell=True)
        vidfile = base_vidfile + str(rec_num).zfill(5)
        vidfile += ".h264  -fps 25 -b 15000000 -vs" #-w 1280 -h 720 -awb tungsten
        print "starting recording\n%s" % vidfile
        time_now = time.time()
        if (time_now - time_off) >= 0.3:
            if front_led_status != 0:
                GPIO.output(5, 1)
            recording = 1
            call ([vidfile], shell=True)
    recording = 0 # only kicks in if the video runs the full period

    #### Quality VS length ###
    # on long clips at max quality you may get dropouts with slow SD cards
    # -w 1280 -h 720 -fps 25 -b 3000000 
    # seems to be low enough to avoid this 

def stop_recording():
    global recording
    global time_off
    time_off = time.time()
    print "stopping recording"
    GPIO.output(5, 0)
    call (["pkill raspivid"], shell=True)
    recording = 0
    if still == 0:
        call ([kill_fbcp], shell=True)
    space_used()     # display space left on recording drive

def space_used():    # function to display space left on recording device
    output_df = subprocess.Popen(["df", "-Ph", "/dev/root"], stdout=subprocess.PIPE).communicate()[0]
    it_num = 0
    for line in output_df.split("\n"):
        line_list = line.split()
        if it_num == 1:
            storage = line_list
        it_num += 1
    print "Card size: %s,   Used: %s,    Available: %s,    Percent used: %s" % (storage[1], storage[2], storage[3], storage[4])
    percent_used = int(storage[4][0:-1])
    if percent_used > 95:
        print "Watch out, you've got less than 5% space left on your SD card!"

# this increments variable rec_num for filename and starts recording
def record_button(channel):
    global rec_num
    time_now = time.time()
    if (time_now - time_off) >= 0.3:
        print "record button pressed"
        rec_num += 1
        if recording == 0:
            write_rec_num(1)
            start_recording(rec_num)

def flash(interval,reps):
    for i in range(reps):
        GPIO.output(5, 1)
        sleep(interval)
        GPIO.output(5, 0)
        sleep(interval)

def shutdown():
    print "shutting down now"
    stop_recording()
    flash(0.05,50)
    GPIO.cleanup()
    os.system("sudo halt")
    sys.exit()

def still_photo(channel):
    global recording, still, photo_num
    if recording == 0:
        still = 1
        print "taking a still" 
        call ([start_fbcp], shell=True)
        photo_num += 1
        write_rec_num(2)
        # set a global so other functions know they can't operate
        recording = 1

        photo_name = str(photo_num).zfill(5)
        cmd = 'raspistill -t 5000 -w 1024 -h 768 -o /home/pi/' + photo_name + '.jpg'  
        print 'cmd ' +cmd
        print "about to take photo"
        call ([cmd], shell=True)
        print "photo taken"
        photo_path = '/home/pi/' + photo_name + '.jpg'

        # stop fbcp
        call ([kill_fbcp], shell=True)
        still = 0

        # process image to make a small preview copy - convert to  31.25%
        print "Making small preview thumbnail 320 x 240"
        thumbnail_path = '/home/pi/' + photo_name + '_320x240.jpg'
        resize = '/usr/bin/convert ' + photo_path + ' -resize 31.25% ' + thumbnail_path
        call ([resize], shell=True)   

        #   Displaying photo we just took for 10 seconds
        show_photo(thumbnail_path, 10) 

        recording = 0

def show_photo(photograph, display_period):
    pygame.init()
    w = 320
    h = 240
    size=(w,h)
    screen = pygame.display.set_mode(size) 
    c = pygame.time.Clock() # create a clock object for timing
    img=pygame.image.load(photograph) 
    screen.blit(img,(0,0))
    pygame.display.flip()
    sleep(display_period)
    pygame.quit()

print "Welcome to the RasPiCamcorder PiTFT edition\n"
print "Button 1: RECORD\n"
print "Button 2: STOP/CLOSE/SHUTDOWN\n"
print "Button 3: SCREEN ON/OFF\n"
print "Button 4: STILL Photo\n"

# Button 1. when a falling edge is detected on port 23 record_button() will be run
GPIO.add_event_detect(23, GPIO.FALLING, callback=record_button)

# Button 3. set up port 21/27 for screen toggle on/off
GPIO.add_event_detect(screen_port, GPIO.FALLING, callback=toggle_screen, bouncetime=300)

# Button 4. set up port 18 to take a still
GPIO.add_event_detect(18, GPIO.FALLING, callback=still_photo, bouncetime=300)

# check rec_num from file
try:
    directory_data = os.listdir("/home/pi/RasPiCamcorderPiTFT")
    if vid_rec_num in directory_data:

        # read file vid_rec_num, make into int() set rec_num equal to it
        vrn = open(vid_rec_num_fp, 'r')
        rec_num = int(vrn.readline())
        print "rec_num is %d" % rec_num
        vrn.close() 

    else:                # if file doesn't exist, create it
        rec_num = 0
        write_rec_num(1) # 1 means video

    if photo_rec_num in directory_data:
        # read file photo_rec_num, make into int() set rec_num equal to it
        prn = open(photo_rec_num_fp, 'r')
        photo_num = int(prn.readline())
        print "photo_num is %d" % photo_num
        prn.close() 
    else:                # if file doesn't exist, create it
        photo_num = 0
        write_rec_num(2) # 2 means photo

except:
    print("Problem listing /home/pi/RasPiCamcorderPiTFT")
    flash(0.1,10)
    GPIO.cleanup()
    sys.exit()

try:
    while True:
        # this will run until button 2, attached to 22 is pressed, then 
        # if pressed >1.25s, close program, if pressed >3s, shutdown Pi
        # stop recording and shutdown gracefully
        print "Waiting for button press"
        GPIO.wait_for_edge(22, GPIO.FALLING)
        print "Stop button pressed"
        stop_recording()

        # poll GPIO 22 button at 20 Hz continuously for 3 seconds
        # if at the end of that time button is still pressed, shut down
        # if it's released at all, break
        for i in range(60):
            if GPIO.input(22):
                break
            sleep(0.05)

        if 25 <= i < 58:              # if released between 1.25 & 3s close prog
            print "Closing program"
            flash(0.02,50) # interval,reps
            call ([cmd_on], shell=True)
            call (['clear'], shell=True)
            print "Thank you for flying with RasPi.TV"
            GPIO.cleanup()
            show_photo('/home/pi/RasPiCamcorderPiTFT/raspitv320x240.jpg', 5)     
            sys.exit()

        if not GPIO.input(22):
            if i >= 59:
                shutdown()

except KeyboardInterrupt:
    stop_recording()
    call ([cmd_on], shell=True)
    GPIO.cleanup()       # clean up GPIO on CTRL+C exit