#!/usr/bin/python
#! -*- coding: utf-8 -*-

import numpy as np

def calculate_T2(sequence, time_1=None, time_2=None):
    """Take DicomSequence and output the same object with t2_slices added.
    
    t2_slices contains a list with with T2 map data stored in
    numpy arrays for each slice.
    """
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
        t2 = t2.astype('>i2')
        t2_seq.append(t2)
        sequence.t2_slices = t2_seq

    return sequence
    
    
def do_T2_math(early_echo, late_echo, time_diff):
    """Takes two numpy arrays and calculates a T2 map. time_diff
    contains TE2 - TE1. This is done one slice at a time.
    """
    early_echo = early_echo.astype('float32')
    late_echo = late_echo.astype('float32')
    div = early_echo / late_echo
    loge = np.log(div)
    t2 = time_diff / loge
    negative_indices = t2 < 0
    t2[negative_indices] = 255.0
    gt_255_indices = t2 > 255
    t2[gt_255_indices] = 255.0
    t2 = t2.astype('>i2')
    return t2
    
def js_interpolate(slice):
    """Takes numpy array and zoom interpolates it to twice its size.
    This is likely bilinear interpolation, but constitutes a clone of an
    interpolation algorithm written by Jay Fahlen.
    """
    rows, cols = slice.shape    
    out = []
    
    for i in xrange(rows):
        if i < rows - 1:
            out.append((slice[i] + slice[i+1]) / 2)
        if i == rows - 1:
            out.append((np.zeros((cols))))
    
    xinter = np.insert(slice, range(1, rows+1), out, axis=0)    
    yinter = np.transpose(xinter)    
    rows, cols = np.transpose(xinter).shape    
    out = []
    
    for i in xrange(rows):
        if i < rows - 1:
            out.append((yinter[i] + yinter[i+1]) / 2)
        if i == rows - 1:
            out.append((np.zeros((cols))))
    
    out = np.asarray(out)
    
    return np.insert(xinter, range(1, len(xinter[0])+1), np.transpose(out), axis = 1)
    
        
def pad_image_to_square(slice):
    """This will take a numpy array and pad with zeros either on the sides or
    top and bottom to make the array square.
    """
    
    rows, cols = slice.shape
        
    if rows > cols:
        diff = rows - cols
        pixel_data = np.zeros((rows, cols + diff), dtype='>i2')
        pixel_data[:, diff/2 : diff/2 + cols] = slice
        
    elif cols > rows:
        diff = cols - rows
        pixel_data = np.zeros((rows + diff, cols), dtype='>i2')
        pixel_data[diff/2 : diff/2 + rows, :] = slice
        
    else:
        pixel_data = slice.astype('>i2')
        
    return pixel_data