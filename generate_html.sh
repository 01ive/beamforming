#!/bin/bash
python generate_animations.py -d 0.5
python generate_animations.py -d 0.4
python generate_animations.py -d 0.6

mv *.html pages
