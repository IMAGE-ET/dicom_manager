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
    #print xinter, '\n\n', yinter, '\n\n',np.asarray(out)
    
    return np.insert(xinter, range(1, len(xinter[0])+1), np.transpose(out), axis = 1)
    
        
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