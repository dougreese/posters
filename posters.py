#!/usr/bin/python
# -*- coding: utf-8 -*- 
#----------------------------------------------------------------------------
# Created By  : Doug Reese (doug@reesesystems.com)
# version ='1.0'

from __future__ import division
import sys
import signal
import os
import pygame
import time
import random
import urllib
import urllib2
from urlparse import urlparse
import hashlib
import os.path
import glob
import time
import ConfigParser 

class GracefulKiller:
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self,signum, frame):
        print 'Received kill notification'
        pygame.quit()
        self.kill_now = True

class pyscope :
    screen = None
    imageList = {}
    
    def __init__(self):
        "Ininitializes a new pygame screen using the framebuffer"
        # Based on "Python GUI in Linux frame buffer"
        # http://www.karoltomala.com/blog/?p=679
        disp_no = os.getenv("DISPLAY")
        if disp_no:
            print "I'm running under X display = {0}".format(disp_no)
        
        # Check which frame buffer drivers are available
        # Start with fbcon since directfb hangs with composite output
        drivers = ['fbcon', 'directfb', 'svgalib']
        found = False
        for driver in drivers:
            # Make sure that SDL_VIDEODRIVER is set
            if not os.getenv('SDL_VIDEODRIVER'):
                os.putenv('SDL_VIDEODRIVER', driver)
            try:
                pygame.display.init()
            except pygame.error:
                print 'Driver: {0} failed.'.format(driver)
                continue
            print 'Driver: {0} succeeded.'.format(driver)
            found = True
            break

        if not found:
            raise Exception('No suitable video driver found!')

        self.config = ConfigParser.ConfigParser()
        self.config.read('posters.ini')

        # no visible cursor 
        pygame.mouse.set_visible(False)

        # initialize to display size
        self.displayWidth = pygame.display.Info().current_w
        self.displayHeight = pygame.display.Info().current_h
        print "Display size: %d x %d" % (self.displayWidth, self.displayHeight)
       
        # read config display size 
#        self.displayWidth = self.config.getint('display', 'resX')
#        self.displayHeight = self.config.getint('display', 'resY')
        
        print "Framebuffer size: %d x %d" % (self.displayWidth, self.displayHeight)
        self.screen = pygame.display.set_mode((self.displayWidth, self.displayHeight), pygame.FULLSCREEN)
        # Clear the screen to start
        self.screen.fill((0, 0, 0))        
        # Initialise font support
        pygame.font.init()
        # Render the screen
        print "Initializing screen..."
        pygame.display.update()

        # create image cache
        self.imageDir = 'images'
        if not os.path.isdir(self.imageDir):
            os.makedirs(self.imageDir)

        self.imageMap = {}
        self.cleanup()
        self.fetchImageList()

    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."
        for url in self.imageList.keys():
            filename = self.imageList[url]
            print "Removing file %s: %s" % (filename, url)
            os.remove(filename)

    def cleanup(self):
        print "Checking for files to cleanup..."
        for fl in glob.glob(self.imageDir + '/' + "image_*"):
            print "Removing file %s" % (fl)
            os.remove(fl)
        # flush output buffer so it gets logged under supervisor
        sys.stdout.flush()
        self.imageMap.clear()

    def fetchImageList(self):
        posterSrc = self.config.get('posters', 'source')
        if ("" == posterSrc):
            raise Exception('No poster source playlist provided.')
        print "Fetching image list from %s" % (posterSrc)
        response = urllib2.urlopen(posterSrc)
        textList = response.read()
        self.images = textList.split("\n")
        print textList
        sys.stdout.flush()

    def fetchImage(self, imageUrl):
        filename = self.imageDir + '/' +'image_' + hashlib.md5(imageUrl).hexdigest()
        if (os.path.isfile(filename) == False):
            print "Fetching %s into file %s" % (imageUrl, filename)
            parts = urlparse(imageUrl)
            filename, headers = urllib.urlretrieve(imageUrl, filename)
            #print headers
            self.imageList[imageUrl] = filename
        print "Have file %s for %s" % (filename, imageUrl)
        sys.stdout.flush()
        return filename

    def rotateImage(self, img):
        img = pygame.transform.rotate(img, 270)
        return img

    def scaleImage(self, img):
        # Scale image to fit
        newWidth = 0
        newHeight = 0
        r = img.get_width() / img.get_height()
        if (self.displayWidth / self.displayHeight > r):
            newWidth = self.displayHeight * r
            newHeight = self.displayHeight
        else:
            newHeight = self.displayWidth / r
            newWidth = self.displayWidth
        # print "Orig image size: %d x %d" % (img.get_width(), img.get_height())
        # print "New image size: %d x %d" % (newWidth, newHeight)
        
        # don't upscale
        if (img.get_width() >= newWidth and img.get_height() >= newHeight):
            img = pygame.transform.scale(img, (int(newWidth), int(newHeight)))
        sys.stdout.flush()
        return img

    def scrollInNew(self):
        incr = self.config.getint('timing', 'transitionPixIncrement')
        xEndCurrent = 0
        xStartCurrent = 0
        xStartNext = self.displayWidth
        xEndNext = (self.displayWidth - self.imgNext.get_width()) / 2
        xNext = xStartNext
        yNext = (self.displayHeight - self.imgNext.get_height()) / 2
        if (self.img):
            xStartCurrent = (self.displayWidth - self.img.get_width()) / 2
            xEndCurrent = 0 - self.img.get_width() - 1
            xCurrent = xStartCurrent
            yCurrent = (self.displayHeight - self.img.get_height()) / 2
        while (xNext > xEndNext):
            scope.screen.fill((0, 0, 0))
            scope.screen.blit(self.imgNext, (xNext, yNext))
            xNext -= incr 
            if (self.img):
                scope.screen.blit(self.img, (xCurrent, yCurrent))
                xCurrent -= incr
            pygame.display.update()
        
        # make sure to draw just the next image
        scope.screen.fill((0, 0, 0))
        scope.screen.blit(self.imgNext, (xEndNext, yNext))
        if (self.img):
            scope.screen.blit(self.img, (xEndCurrent, yCurrent))
        pygame.display.update()
        
        self.img = self.imgNext

    def letsgo(self):
        killer = GracefulKiller()
        self.img = None
        imgCnt = len(self.images)
        i = 0
        displayTime = self.config.getint('timing', 'displayTime')
        startTime = time.time()
        refreshInterval = self.config.getint('timing', 'refreshInterval')
        print "Images will refresh in %d seconds" % refreshInterval
        while not killer.kill_now:
            try:
                imgUrl = self.images[i]
                imgFile = self.fetchImage(imgUrl)
                self.imgNext = pygame.image.load(imgFile).convert()
                self.imgNext = self.rotateImage(self.imgNext)
                self.imgNext = self.scaleImage(self.imgNext)
                self.scrollInNew()
                sys.stdout.flush()
                time.sleep(displayTime)
            except:
                print "Error displaying image %s" % imgUrl
            i += 1
            runTime = time.time() - startTime
            print "Elapsed time: %d" % runTime
            if (runTime > refreshInterval):
                try:
                    self.fetchImageList()
                    imgCnt = len(self.images)
                    self.cleanup()
                except:
                    print "Error fetching image list, restarting refresh timer."
                startTime = time.time()
            if (i >= imgCnt):
                i = 0

# Clear screen
print(chr(27) + "[2J")

# Create an instance of the PyScope class
scope = pyscope()
scope.letsgo()
print 'Quitting.'
sys.stdout.flush()
exit(0)

