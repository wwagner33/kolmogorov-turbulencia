#!/bin/bash

ffmpeg -framerate 60 -i capturas/img_%05d.png -c:v libx264 -pix_fmt yuv420p simulacao$(date +"%Y%m%d-%H_%M").mp4
