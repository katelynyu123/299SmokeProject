#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 2019

Location Bounding for PurpleAir Data

@author: Alex
"""

# Libraries
import glob
import os.path
import pandas
import decimal

# Function to move find files in the desired location bounding box.
def location_clip(data_path, dest_path, )