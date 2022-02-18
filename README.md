# Posters

## Overview

The Posters project was originally developed to display a list of poster images on monitors mounted vertically outside a music venue.  

The system runs on a Raspberry Pi, but should work on any system with a monitor.  The list of images to display are fetched from a URL, and the list is updated periodically at a specified interval.

## Setup

Copy `posters.ini.example` to `posters.ini` and set the `source` in the `[posters]` section to the URL containing a list of posters.  In the original system this list was generated dynamically, but it could be a static text file.

Adjust any other settings in either `posters.ini` as necessary.

## Run

Run `posters.py`, or set up a process control system, such as [Supervisor](http://supervisord.org/) or a [systemd](https://systemd.io/) service to manage the running process. 

The `posters.conf` is an example Supervisor config for running the process on startup and keeping it running.
