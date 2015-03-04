#!/usr/bin/python
import os
import sys
from struct import *
from distutils.util import strtobool
from dataset import DicomDataset

"""
MedVision file structure is as follows:
	-MedVision study header (24 bytes)
		-Consists of mv_head_1 + number of slices (2 bytes) + mv_head_2
	-Slice header (10 Bytes)
		-Consists of #Rows(2 bytes) + #Columns(2 bytes) + sl_head_part 8 or
		 16 bits depending on data (2 bytes) + two_zeros (2 bytes) + slice 
		 number (2 bytes)
	-Pixel data (2 bytes per pixel if 16bit, 1byte if 8bit)
	-Slice header
	-Pixel data
	-etc.	
"""

mv_head_1 = 'MVSTUDY \x00\x00\x00x\x00\x00\x00\x18'
mv_head_2 = '\x00\n\x00\x00\x00\x00'
sl_head_part_8bit = ' \x01'
sl_head_part_16bit = '\x10\x02'
two_zeros = '\x00\x00'

def convert(data, sequence_path, do_all, interp = True):
    sequence = data.make_sequence(sequence_path)
    print "\n............................................................"
    print 'Subject ID            : ' + str(sequence.info("PatientName"))
    print 'Sequence Number       : ' + str(sequence.info("SeriesNumber"))
    print 'Sequence Description  : ' + str(sequence.info("SeriesDescription"))
    size = str(sequence.info('Rows')) + 'x' + str(sequence.info('Columns'))
    print 'Image Size (Rows/Cols): ' + size
    base_name = raw_input("Enter base name for MV file. ")
    

def user_yes_no_query(question):
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
    
    print "\n............................................................"
    print "Found {0} sequence(s).".format(len(data.seq_list))
    do_all = user_yes_no_query("Convert all?")
    
    for sequence_path in data.seq_list:
        convert(data, sequence_path, do_all)


        
