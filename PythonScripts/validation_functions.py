#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation Functions

@author: Alex Young
"""

### Load Libraries
import pandas as pd
import numpy as np
import datetime as dt
import glob

### Replace spaces in file names with '#' for standardization.
def replace_with_pound(space_path, pound_path, name_loc):
    # Create path to loop through.
    space_glob_path = space_path +'*'# add "+ '*.csv'" instead if files are in csv format 
    files = glob.glob(space_glob_path)
    
    for file in files:
        # Get sensor name from full file path.
        path_split = file.split('\\') #replace with ('/') for MacOS
        sensor_name = path_split[name_loc] # Needs to be the correct position.
    
        # Split name at spaces to get rid of spaces in filename.
        split_name = sensor_name.split(' ')
        split_name = [i for i in split_name if i != '']
        
        # Replaces spaces with #.
        p_name = '#'.join(split_name)
        p_name_path = pound_path + p_name
        
        # Write new no-space files to Data_In_Box_No_Spaces.
        # Open original file.
        orig = open(file, 'r')
        new = open(p_name_path, 'w+')
        # Write lines from original file into new file.
        for line in orig:
            new.write(line)
        # Close files.
        orig.close()
        new.close()
        
### Check if files have points in the desired range of time.
def time_range(t_init, t_fin, file_path, time_path, name_loc):
    # Create path to loop through.
    file_glob_path = file_path +'*' # add "+ '*.csv'" instead if files are in csv format 
    files = glob.glob(file_glob_path)
    
    #issue_count = 0 # Number of files that did not contain range.
    for file in files: # Access files in Data_In_Box_No_Spaces.
        df = pd.read_csv(file) # Make Dataframe.
        df['created_at'] = pd.to_datetime(df['created_at'])
        if df.empty == False:
            if df['created_at'].iloc[0] > t_init and df['created_at'].iloc[-1] < t_fin:
                # Make a new file from the file with correct range.
                # Make sure to not include files that if they don't have a corresponding channel.
                # Might make more sense to do this first. Then run the two channel function.
                file_name = file.split('\\')[name_loc] # Get name1 file name without path.
                range_name = time_path + file_name # New path to file.

                f = open(file, 'r')
                n = open(range_name, 'w')

                for line in f:
                    n.write(line)

                f.close()
                n.close()
            else: 
                print(file + 'not in range')
        else:
            print(file + 'is an empty file')
            issue_count += 1
            
            
### Only use files that have the PM2.5_CF_1_ug/m3 unit.
### May take out this function depending on conversions.            
def correct_units(file_path, unit_path, name_loc):
    # Create path to loop through.
    file_glob_path = file_path + '*'# add "+ '*.csv'" instead if files are in csv format 
    files = glob.glob(file_glob_path)
    
    for file in files:
        df = pd.read_csv(file)
        
        # Get column list.
        columns = list(df)
        
        # Get files that have correct units in header.
        if "PM2.5_CF1_ug/m3" in columns:
            f_name = file.split('\\')[name_loc] # Get name1 file name without path.
            unit_name = unit_path + f_name # New path to file.
            
            f = open(file, 'r')
            n = open(unit_name, 'w')
            
            for line in f:
                n.write(line)
            
            f.close()
            n.close()
            
### Interpolate to Time Standard
def time_interpolate(t_init, t_fin, file_path, interp_path, name_loc):
    # Create path to loop through.
    file_glob_path = file_path +'*'# add "+ '*.csv'" instead if files are in csv format 
    files = glob.glob(file_glob_path)
    
    # Range of time as datetime objects.
    t_init = pd.to_datetime(t_init)
    t_fin = pd.to_datetime(t_fin)
    total_time = int((t_fin-t_init).total_seconds()/3600)
    
    # Create Time Standard.
    time_standard = []
    hour_count = 0
    for i in range(total_time+1):
        td = dt.timedelta(hours = hour_count) # Time delta of 1 hour.
        time_standard.append(t_init + td) # Add number of hours.
        
        hour_count += 1
        
    # Create a time standard in Unix format.
    time_standard_unix = np.array(pd.to_datetime(time_standard)).astype(np.int64) // 10**9
        
    # Interpolate files to time standard. Export new files to interpolated folder.
    # Using numpy linear interpolation.
    for file in files:
        # Read in data.
        df = pd.read_csv(file)
        
        # Make the time column and reading column into np arrays. Convert to Unix first.
        unix_times = np.array(pd.to_datetime(df['created_at']).astype(np.int64)) // 10**9
        zp = np.array(df['PM2.5_CF1_ug/m3'])
        
        # Interpolate to time_standard times.
        pm25_interp = np.interp(time_standard_unix, unix_times, zp)
        
        # Create new Dataframe with time standard and PM 2.5 values
        d = {'SAMPLE_TIME_UTC': time_standard, 'PM_2.5_ug/m3': pm25_interp}
        df_interp = pd.DataFrame(data=d)
        
        # Add to Data_In_Box_Interpolated folder.
        file_name = file.split('\\')[name_loc]
        complete_path = interp_path + file_name
        
        df_interp.to_csv(complete_path, index = False)
        
### Get all sensors with both channels.
def two_channel(file_path, two_channel_path, name_loc):
    # Create path to loop through.
    file_glob_path = file_path +'*'# add "+ '*.csv'" instead if files are in csv format 
    files = glob.glob(file_glob_path)
    
    # Initialize some variables.
    no_match_number = 0 # How many files don't have second channel file.
    no_match = 1 # Switch for counting non matches.
    
    for file1 in files:
        # Need to add B to name to in order to test.
        # Name convention Channel A: "my sensor#_lat_lon.csv", Channel B: "my sensor#B#_lat_lon.csv"
        split_name = file1.split('#')
        # Only look for Channel A and then corresponding Channel B. Looking for both will double count.
        if 'B' not in split_name: # This finds channel A.
            # Create corresponding B channel name to look for.
            file1_test = '#'.join(split_name[:-1]) + '#' + 'B' + '#' + str(split_name[-1])
            
            # Search for corresponding channel B.
            no_match = 1 # no_match counter.
            for file2 in files:
                # Test for a match.
                if file1_test == file2:
                    no_match = 2 # Switch no_match because match was found.
                    
                    # Put both channels into the folder.
                    # Validated names.
                    file1_name = file1.split('\\')[name_loc] # Get name1 file name without path.
                    file2_name = file2.split('\\')[name_loc] # Get name2 file name without path.
                    channel_name1 = two_channel_path + file1_name # New path to file.
                    channel_name2 = two_channel_path + file2_name # New path to file.
                    
                    # Open new files.
                    c1 = open(channel_name1, 'w')
                    c2 = open(channel_name2, 'w')
                    
                    # Open working files.
                    n1 = open(file1,'r')
                    n2 = open(file2,'r')
                    
                    for line in n1:
                        c1.write(line)
                    for line in n2:
                        c2.write(line)
                    
                    # Close files.
                    c1.close()
                    c2.close()
                    n1.close()
                    n2.close()
        
        # If there were no matches, increment no_match_number.
        if no_match == 1:
            no_match_number += 1
            
### Sensor validation by comparing channels.
def validate_sensors(file_path, validated_path, tolerance, name_loc):
    # Create path to loop through.
    file_glob_path = file_path +'*'# add "+ '*.csv'" instead if files are in csv format 
    files = glob.glob(file_glob_path)
    
    tol = 10 # Tolerance.
    for name1 in files:
        # Need to add B to name to in order to test.
        # Name convention Channel A: "my sensor#_lat_lon.csv", Channel B: "my sensor#B#_lat_lon.csv"
        split_name = name1.split('#')
        # Only look for Channel A and then corresponding Channel B. Looking for both will double count.
        if 'B' not in split_name: # This finds channel A.
            # Create corresponding B channel name to look for.
            name1_test = '#'.join(split_name[:-1]) + '#' + 'B' + '#' + str(split_name[-1])
            
            # Search for corresponding channel B.
            for name2 in files:
                # Test for a match.
                if name1_test == name2: # Find Corresponding B Channel.
                    # Create 2 dataframes from each channel.
                    df1 = pd.read_csv(name1)
                    df2 = pd.read_csv(name2)
                    
                    # Make numpy arrays of the concentration columns and average.
                    conc1 = np.array(df1['PM_2.5_ug/m3'])
                    conc2 = np.array(df2['PM_2.5_ug/m3'])
                    
                    avg_conc = (conc1 + conc2) / 2
                    avg_df = df1
                    avg_df['PM_2.5_ug/m3'] = avg_conc
                    
                    # Find the difference of all values.
                    diffs = abs(conc1 - conc2)
                    
                    # If all values are below the tolerance, keep the files.
                    if np.amax(diffs) < tolerance:
                        # Get file names without path.
                        file_name1 = name1.split('\\')[name_loc]
                        
                        # Get the lat and lon and add them to the dataframe.
                        latlon_split = file_name1.split('_')
                        lat = latlon_split[1]
                        lon = latlon_split[2][:-4]
                        avg_df['lat'] = lat
                        avg_df['lon'] = lon
                        
                        path1 = validated_path + 'AVG#' + file_name1
                        #file_name2 = name2.split('/')[name_loc]
                        #path2 = validated_path + file_name2
                        
                        # Add channels to the folder.
                        avg_df.to_csv(path1, index = False)
                        #df2.to_csv(path2)
                        
"""
Amended by @author: Katelyn Yu

"""

def Title_format(space_path, title_path, name_loc):
    # Create path to loop through.
    space_glob_path = space_path + '*.csv'
    files = glob.glob(space_glob_path)
    
    for file in files:
        # Get sensor name from full file path.
        path_split = file.split('\\') #replace with ('/') for MacOS
        sensor_name = path_split[name_loc] # Needs to be the correct position.
    
        # Extract lat and lon values from the title 
        latlon= sensor_name[sensor_name.rfind("(")+1:sensor_name.rfind(")")] #rfind finds from the end rather than beginning
        latlon = latlon.split(' ')

        lat = latlon[0]
        lon = latlon[1]
        
        #Getting location alone + one space
        loc = sensor_name[0:sensor_name.find("(")]
        
        #Adding A or B and creating name to match original title format 
        if "Primary" in sensor_name:
            title = loc + "A_" + lat + '_' + lon
        elif "Secondary" in sensor_name:
            title = loc + "B_" + lat + '_' + lon
        
        t_name_path = title_path + title

        # Write fixed title to  to Data_In_Box_TitleFormatted.
        # Open original file.
        orig = open(file, 'r')
        new = open(t_name_path, 'w+')
        # Write lines from original file into new file.
        for line in orig:
            new.write(line)
        # Close files.
        orig.close()
        new.close()
