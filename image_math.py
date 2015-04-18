#!/usr/bin/python
#! -*- coding: utf-8 -*-

import numpy as np

def calculate_T2(sequence, time_1=None, time_2=None):
    if time_1 == time_2 == None:
        echo_times = []
        for i in sequence.split_ds:
            echo_times.append(i[1])
        
        time_1 = min(echo_times)
        time_2 = max(echo_times)
        
    time_1 = int(time_1)
    time_2 = int(time_2)
    time_1_seq = sequence.split_ds['EchoTime', str(time_1)]
    time_2_seq = sequence.split_ds['EchoTime', str(time_2)]

    t2_seq = []
    
    for n in xrange(len(time_1_seq)):
        
        early_echo = time_1_seq[n][0].pixel_array.astype('float32')
        late_echo = time_2_seq[n][0].pixel_array.astype('float32')
        div = early_echo / late_echo
        loge = np.log(div)
        time_diff = time_2 - time_1
        t2 = time_diff / loge
        negative_indices = t2 < 0
        t2[negative_indices] = 255.0
        gt_255_indices = t2 > 255
        t2[gt_255_indices] = 255.0
        t2 = t2.astype('uint16', order='C')
        t2_seq.append(t2)
        sequence.t2_slices = t2_seq

    return sequence
    
    
def js_interpolate(slice):
    
    
    '''slice_y_interp = slice.copy()
    
    for row_num in xrange(len(slice_y_interp)-1):
        if row_num < len(slice_y_interp) - 1:
            slice_y_interp = np.insert(slice_y_interp, 0, (slice[row_num]+ slice[row_num+1])/2, axis=0)
        else:
            slice_y_interp = np.insert(slice_y_interp, 0, slice[row_num] ,axis=0)
    
    slice_xy_interp = np.transpose(slice_y_interp)
        
    for row_num in xrange(len(slice_xy_interp)):
        if row_num < len(slice_xy_interp) - 1:
            slice_xy_interp = np.insert(slice_xy_interp, 0, (slice_y_interp[row_num]+ slice_y_interp[row_num+1])/2, axis=0)
        else:
            slice_xy_interp = np.insert(slice_xy_interp, 0, slice[row_num], axis=0)
   
    interp_slice = np.transpose(slice_xy_interp)
    
    
    print interp_slice.shape
    
    return interp_slice'''
    return slice
    
def pad_image_to_square(slice):
    
    rows, cols = slice.shape
    
    if rows > cols:
        diff = rows - cols
        pixel_data = np.zeros((rows, cols + diff), dtype='uint16')
        pixel_data[:, diff/2 : diff/2 + cols] = slice
        
    elif cols > rows:
        diff = cols - rows
        pixel_data = np.zeros((rows + diff, cols), dtype='uint16')
        pixel_data[diff/2 : diff/2 + rows, :] = slice
        
    else:
        pixel_data = slice
        
    return pixel_data