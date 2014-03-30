RasPiCamcorderPiTFT
===================

RasPiCamcorder3 the PiTFT version

This sofware is intended to be used with a Raspberry Pi, Pi camera and the Adafruit PiTFT screen with four buttons attached.

![RasPiCamcorder Photo](http://raspi.tv/wp-content/uploads/2014/03/DSC_0604_700.jpg "RasPiCamcorder 3")

I'm also using the Pimoroni http://shop.pimoroni.com/products/pitft-pibow designed to fit the PiTFT.

###Assemble and install your PiTFT ###
http://learn.adafruit.com/adafruit-pitft-28-inch-resistive-touchscreen-display-raspberry-pi/
You will need four slim buttons to use this script.

But don't set up a power off button. We need them all, and we have one of those already. 
Button 2 acts as 'stop' if pressed momentarily, 'close program' if pressed for more than 1.25 seconds and 'shutdown Pi' if pressed for >3 seconds.


###Install fbcp###

For the live screen output to work, you need fbcp.

https://github.com/tasanakorn/rpi-fbcp

You can download and compile it yourself (the instructions are quite good, but you will need to install cmake with `sudo apt-get install cmake`).
Or you can use the binary file provided here called fbcp. It's in the /home/pi/RasPiCamcorderPiTFT directory. 


###Install imagemagick###
You need this for the resizing of preview stills to 320x240
`sudo apt-get install imagemagick`

###How To Intall This Software###
`cd ~`
`git clone https://github.com/raspitv/RasPiCamcorderPiTFT`

You should have git installed already, but if not...
`sudo apt-get install git-core`


###How to make it auto start on boot###
`sudo nano /etc/rc.local`

Then, before the line where it says 'exit 0', insert this...

`/home/pi/RasPiCamcorderPiTFT/picamcorder3.py`


###How to run it###
From the command line...

`sudo python /home/pi/RasPiCamcorderPiTFT/picamcorder3.py`
or navigate to /home/pi/RasPiCamcorderPiTFT and type...
`sudo python picamcorder3.py`

The sudo is needed because we're using GPIO.


