#!/usr/bin/python
#! -*- coding: utf-8 -*-

import os
import sys
import cPickle as pickle
import numpy as np
import scipy.ndimage as ndimage
from struct import *
from distutils.util import strtobool
from dataset import DicomDataset
from image_math import calculate_T2


"""
MedVision file structure is as follows:
    -MedVision study header (24 bytes)
        -Consists of mv_head_1 + number of slices (2 bytes) + mv_head_2
    -Slice header (10 Bytes)
        -Consists of #Rows(2 bytes) + #Columns(2 bytes) + sl_head_part - 8 or
         16 bits depending on data (2 bytes) + two_zeros (2 bytes) + slice 
         number (2 bytes)
    -Pixel data (2 bytes per pixel if 16bit, 1 byte if 8bit)
    -Slice header
    -Pixel data
    -etc.    
"""

mv_head_1 = 'MVSTUDY \x00\x00\x00x\x00\x00\x00\x18'
mv_head_2 = '\x00\n\x00\x00\x00\x00'
sl_head_part_8bit = ' \x01'
sl_head_part_16bit = '\x10\x02'
two_zeros = '\x00\x00'

naming_dict = pickle.load(open('dat/naming_dict.p', 'rb'))

def convert(data, sequence_path, do_all, interp = True):
    
    sequence = data.make_sequence(sequence_path)
    print '\n............................................................'
    print 'Subject Name          : '  + str(sequence.info('PatientName'))
    print 'Subject ID            : '  + str(sequence.info('PatientID'))
    print 'Sequence Number       : '  + str(sequence.info('SeriesNumber'))
    print 'Sequence Description  : '  + str(sequence.info('SeriesDescription'))
    print 'Sequence Type         : '  + str(sequence.info('ScanningSequence'))
    image_size = str(sequence.info('Rows')) + 'x' + str(sequence.info('Columns'))
    print 'Image Size (Rows/Cols): '  + image_size
    print 'Number of Slices      : '  + str(sequence.size()['main'])
    
    if not do_all:
        if not user_yn_query('Convert this sequence?'):
            print "Sequence skipped."
            return
            
    if sequence.info('ScanningSequence') == 'SE':
        if do_all:
            print '\nSpin Echo sequence detected. Splitting sequence by Echo Time.'
            print '\tSequence split into:'
            sequence.split('EchoTime')
            split_size = sequence.size()
            for block in split_size:
                print '\t\t{0}: {1} slices'.format(block, split_size[block])
            print '\n'
            if len(split_size) == 2:
                t2_pixels = calculate_T2(sequence.split_ds)
                basename = get_basename(sequence)
                make_MV_file(t2_pixels, basename, is_t2 = True)

   
            elif len(split_size) > 2:
                print 'More than two echoes found.'
                for block in split_size:
                    print '\t\t{0}: {1} slices'.format(block, split_size[block])
                question = 'Enter two echo times you wish to make into T2 (e.g. 22, 90)'
                echo_times_to_make_into_T2 = raw_input(question)
                time_1 = echo_times_to_make_into_T2[0]
                time_1 = echo_times_to_make_into_T2[1]
                basename = get_basename(sequence)
                make_MV_file(sequence, basename)
                t2_pixels = calculate_T2(sequence.split_ds, time_1, time_2)
                basename = get_basename(sequence)
                make_MV_file(t2_pixels, basename, is_t2 = True)
                
            elif len(split_size) == 1:
                print 'Only one block found after split.'
                convert_original = user_yn_query('Convert original? (if no sequence will be skipped)')
                if convert_original:
                    basename = get_basename(sequence)
                    make_MV_file(sequence, basename)
                else:
                    print 'Sequence skipped.'
                    return
                
                
        if not do_all:
            question ='\nSpin Echo sequence detected. Split the sequence by Echo Time?'
            split_the_sequence = user_yn_query(question)
            if split_the_sequence:
                print 'Splitting sequence by Echo Time.'
                print '\tSequence split into:'
                sequence.split('EchoTime')
                split_size = sequence.size()
                for block in split_size:
                    print '\t\t{0}: {1} slices'.format(block, split_size[block])
            if not split_the_sequence:
                make_concat_MV = user_yn_query('Convert sequence into MV wiihtout splittin?')
                if make_concat_MV:
                    basename = get_basename(sequence)
                    make_MV_file(sequence, basename)
                if not make_concat_MV:
                    print "Sequence skipped"
                    return
    basename = get_basename(sequence)
    make_MV_file(sequence, basename)

def get_basename(sequence):    
    if sequence.info('SeriesDescription') not in naming_dict:
        base_name = raw_input('Enter base name for MV file. ')
        naming_dict[sequence.info('SeriesDescription') ] = base_name
    else:
        base_name = naming_dict[sequence.info('SeriesDescription')]        
    return base_name
    
    
def make_MV_file(sequence, basename, is_t2 = False):
    if is_t2:
        print basename
   
    elif not is_t2:
        slice_number = 0
        number_of_slices = len(sequence.ds)
        outpath = sequence.path + '/' + basename
        open(outpath, 'a').write(mv_head_1)
        open(outpath, 'a').write(pack('H', number_of_slices))
        open(outpath, 'a').write(mv_head_2)
   
        for i in sequence.ds:
            rows = i[0].Rows
            cols = i[0].Columns
            diff = rows - cols               
            open(outpath, 'a').write(pack('H', rows))
            open(outpath, 'a').write(pack('H', cols + diff))
            open(outpath, 'a').write(sl_head_part_16bit)
            open(outpath, 'a').write(two_zeros)
            open(outpath, 'a').write(pack('H', slice_number))
            
            
            if rows!= cols:
                pixel_data = np.zeros((rows, rows + diff))
                pixel_data[:, diff/2 : diff/2 + cols] = i[0].pixel_array
            else:
                pixel_data = i[0].pixel_array.copy()
            
            with open(outpath, 'a') as f:
                for n in pixel_data.flat:

                    f.write(pack('H', n))
            slice_number += 1
    
def user_yn_query(question):
    sys.stdout.write('%s [y/n] ' % question)
    while True:
        try:
            return strtobool(raw_input().lower())
        except ValueError:
            sys.stdout.write('Please respond with \'y\' or \'n\'. ')

if __name__ == '__main__':

    data = DicomDataset()
    data.ask_for_source_dir()
    data.get_seq_list()
    
    print '\n............................................................'
    print 'Found {0} sequence(s):'.format(len(data.seq_list))
    for sequence_path in data.seq_list:
        print sequence_path
        
    do_all = user_yn_query('Convert all?')
    
    for sequence_path in data.seq_list:
        convert(data, sequence_path, do_all)
