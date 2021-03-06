#!/usr/bin/python
#! -*- coding: utf-8 -*-

import os
import sys
import cPickle as pickle
import numpy as np
import nibabel as nb
from struct import *
from image_math import *
from string import split
from distutils.util import strtobool
from dataset import ImageDataset


naming_dict = pickle.load(open('dat/naming_dict.p', 'rb'))

def convert_NIFTI(data, nifti_path, do_all):
    
    if do_all:
        for file in data.nii_list[nifti_path]:
            file_path = os.path.join(nifti_path, file)
            img = nb.load(file_path)
            img_data = img.get_data()
            
            if np.min(img_data) < 0:
                print file, ' - negative values detected!!!'
                img_data = img_data * 2 + 4096 #slope = 2, intercept = 4096

            if len(img_data.shape) == 3:
                num_slices = img_data.shape[-1]
            
                num_slices = '(' + str(num_slices) + ')'
                outpath = os.path.join(nifti_path, split(file, sep='.')[0]) + num_slices
                write_MV_file(np.transpose(np.fliplr(img_data), (2, 1, 0)), outpath)
                inter_slices = []
                for slice in np.transpose(np.fliplr(img_data), (2, 1, 0)):
                    inter_slices.append(js_interpolate(slice))
                write_MV_file(inter_slices, outpath + '_inter')
            
            elif len(img_data.shape) == 4 and img_data.shape[3] == 2:
                num_slices = img_data.shape[-2]
                num_slices = '(' + str(num_slices) + ')'
                print '2 volumes are detected in {0}'.format(file)
                make_T2 = user_yn_query('Would you like to make a T2 image out of these?')
                
                outpath = os.path.join(nifti_path, split(file, sep='.')[0])
               
                if make_T2:
                    question = 'Enter two echo times one for each volume (e.g. 22, 90)' 
                    times = input(question)
                    time_diff = int(times[1]) - int(times[0])
                    t2_img = do_T2_math(img_data[::, ::, ::, 0], img_data[::, ::, ::, 1], time_diff)
                    outpath = outpath + 'T2'
                    
                    write_MV_file(np.transpose(np.fliplr(t2_img), (2, 1, 0)), outpath + num_slices)
                    inter_slices = []
                    for slice in np.transpose(np.fliplr(t2_img), (2, 1, 0)):
                        inter_slices.append(js_interpolate(slice))
                    write_MV_file(inter_slices, outpath + num_slices + '_inter')
                
                    outpath = os.path.join(nifti_path, split(file, sep='.')[0])
                
                    for i in xrange(img_data.shape[3]):
                        img_data_c = img_data[::, ::, ::, i]
                    
                        write_MV_file(np.transpose(np.fliplr(img_data_c), (2, 1, 0)), outpath  + str(times[i]) + num_slices)
                        inter_slices = []
                        for slice in np.transpose(np.fliplr(img_data_c), (2, 1, 0)):
                            inter_slices.append(js_interpolate(slice))
                        write_MV_file(inter_slices, outpath + str(times[i]) + num_slices + '_inter')
                            
    return

def convert_DICOM(data, sequence_path, do_all, interp = True):
    
    
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
                basename = get_basename(sequence)
            
                make_MV_file(calculate_T2(sequence), basename, is_t2 = True)
                return

   
            elif len(split_size) > 2:
                print 'More than two echoes found.'
                for block in split_size:
                    print '\t\t{0}: {1} slices'.format(block, split_size[block])
                question = 'Enter two echo times you wish to make into T2 (e.g. 22, 90)'
                echo_times_to_make_into_T2 = input(question)
                time_1 = echo_times_to_make_into_T2[0]
                time_2 = echo_times_to_make_into_T2[1]
                basename = get_basename(sequence)
                make_MV_file(calculate_T2(sequence, time_1, time_2), basename, is_t2 = True)
                return
                
            elif len(split_size) == 1:
                print 'Only one block found after split.'
                convert_original = user_yn_query('Convert original? (if no sequence will be skipped)')
                if convert_original:
                    basename = get_basename(sequence)
                    make_MV_file(sequence, basename)
                    return
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
                basename = get_basename(sequence)
                make_MV_file(calculate_T2(sequence), basename, is_t2 = True)

                return
                
            if not split_the_sequence:
                make_concat_MV = user_yn_query('Convert sequence into MV without splitting?')
                if make_concat_MV:
                    basename = get_basename(sequence)
                    make_MV_file(sequence, basename)
                    return
                if not make_concat_MV:
                    print "Sequence skipped"
                    return
    
    basename = get_basename(sequence)
    make_MV_file(sequence, basename)
    return
    

def get_basename(sequence):    
    if sequence.info('SeriesDescription') not in naming_dict:
        base_name = raw_input('Enter base name for MV file. ')
        naming_dict[sequence.info('SeriesDescription') ] = base_name
    else:
        base_name = naming_dict[sequence.info('SeriesDescription')]        
    return base_name
    
    
def make_MV_file(sequence, basename, is_t2 = False):

    if is_t2:

        number_of_slices = len(sequence.t2_slices)
        outpath = os.path.dirname(sequence.path) + '/' + str(sequence.info('SeriesNumber')) + '_' + basename + 'T2' + '(' + str(number_of_slices) + ')'
        write_MV_file(sequence.t2_slices, outpath)
        
        inter_slices = []
        for slice in sequence.t2_slices:
            inter_slices.append(js_interpolate(slice))
        write_MV_file(inter_slices, outpath+'_inter')
            
        for block in sequence.split_ds:
            number_of_slices = len(sequence.split_ds[block])
            outpath = os.path.dirname(sequence.path) + '/' + str(sequence.info('SeriesNumber')) + '_' + basename + str(block[1]) + '(' + str(number_of_slices) + ')'
            write_MV_file(sequence.split_ds[block], outpath)
            
            inter_slices = []
            for slice in sequence.split_ds[block]:
                inter_slices.append(js_interpolate(slice[0].pixel_array))
            write_MV_file(inter_slices, outpath+'_inter')
            
    elif not is_t2:
        number_of_slices = len(sequence.ds)
        outpath = os.path.dirname(sequence.path) + '/' + str(sequence.info('SeriesNumber')) + '_' + basename + '(' + str(number_of_slices) + ')'
        write_MV_file(sequence.ds, outpath)
        
        inter_slices = []
        
        for slice in sequence.ds:
            slice = pad_image_to_square(slice[0].pixel_array)
            inter_slices.append(js_interpolate(slice))
        write_MV_file(inter_slices, outpath+'_inter')
    
    return
    
    
def write_MV_file(ds_list, outpath):

    """MedVision file structure is as follows:
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
        MEDVISION IS BIG-ENDIAN!
    """

    #mv_head_1 = 'MVSTUDY \x00\x00\x00x\x00\x00\x00\x18'
    mv_head_1 = np.asarray([77, 86, 83, 84, 85, 68, 89, 32, 0, 0, 0, 120, 0, 0, 0, 24], dtype='>i1')
    
    #mv_head_2 = '\x00\n\x00\x00\x00\x00'
    mv_head_2 = np.asarray([0, 10, 0, 0, 0, 0], dtype='>i1')
    #sl_head_part_8bit = ' \x01'
    sl_head_part_8bit = np.asarray([32, 1], dtype='>i1')
    #sl_head_part_16bit = '\x10\x02'
    sl_head_part_16bit = np.asarray([16, 2], dtype='>i1')
    #two_zeros = '\x00\x00'
    two_zeros = np.asarray([0, 0], dtype='>i1')
    
    slice_number = 0
    number_of_slices = len(ds_list)
    open(outpath, 'ab').write(mv_head_1.tobytes())
    open(outpath, 'ab').write(pack('>H', number_of_slices))
    open(outpath, 'ab').write(mv_head_2.tobytes())

    if len(ds_list[0]) == 2:
        final_list = []
        for i in ds_list:
            final_list.append(i[0].pixel_array)
                
    else:
        final_list = ds_list
    
    for slice in final_list:
        
        pixel_data = pad_image_to_square(slice)
        rows, cols = pixel_data.shape
            
        open(outpath, 'ab').write(pack('>H', rows))
        open(outpath, 'ab').write(pack('>H', cols))
        open(outpath, 'ab').write(sl_head_part_16bit.tobytes())
        open(outpath, 'ab').write(two_zeros.tobytes())
        open(outpath, 'ab').write(pack('>H', slice_number))
                       
        with open(outpath, 'ab') as f:
            f.write(pixel_data.tobytes())
            
        slice_number += 1

def user_yn_query(question):
    sys.stdout.write('%s [y/n] ' % question)
    while True:
        try:
            return strtobool(raw_input().lower())
        except ValueError:
            sys.stdout.write('Please respond with \'y\' or \'n\'. ')

if __name__ == '__main__':

    data = ImageDataset()
    data.ask_for_source_dir()
    data.get_seq_list()
    
    if data.nii_list:
        print 'Found NIFTI file(s).'
        do_all = user_yn_query('Convert?')
        
        for nifti_path in data.nii_list:
            convert_NIFTI(data, nifti_path, do_all)
    
    
    
    print '\n............................................................\n'
    
    if data.seq_list:
        print 'Found {0} DICOM sequence(s):'.format(len(data.seq_list))
        for sequence_path in data.seq_list:
            print sequence_path
        
        do_all = user_yn_query('Convert all?')
    
        for sequence_path in data.seq_list:
            convert_DICOM(data, sequence_path, do_all)
    else:
        print 'No DICOM sequences found in specified directory.'