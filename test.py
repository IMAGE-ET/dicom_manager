#!/usr/bin/python
#! -*- coding: utf-8 -*-

import os
import unittest as ut

from dataset import DicomDataset

home_folder = os.getcwd()+'/test_dicom'
for root, dirs, files in os.walk(home_folder):
    if len(dirs) == 0 and files[1].endswith('.dcm'):
        test_sequence = root
        break

class DicomDatasetTest(ut.TestCase):

    def setUp(self):
        self.app = DicomDataset(home_folder)
        self.app.get_seq_list()
        self.seq_dir = test_sequence
    
    def test_dataset_assigns_main_dir_correctly(self):
        self.assertEqual(self.app.main_dir, home_folder)
        
    def test_dataset_seq_list_not_empty(self):
        self.assertFalse(len(self.app.seq_list) == 0)
   
    def test_dataset_has_correct_number_of_files(self):
        number_of_files = len(self.app.seq_list[test_sequence])
        sequence = self.app.make_sequence(self.seq_dir)
        self.assertEqual(number_of_files, 26)
        
    def test_sequence_items_are_pydicom_datasets(self):
        sequence = self.app.make_sequence(self.seq_dir)
        self.assertEqual(sequence.info('PatientID'), 'yI1Yf6zek5U')
        self.assertEqual(sequence.info(tag=[0x10, 0x10]), 'MRIX LUMBAR')
        
    def test_sequence_size_method(self):
        sequence = self.app.make_sequence(self.seq_dir)
        number_of_files = len(self.app.seq_list[test_sequence])
        self.assertIsInstance(sequence.size(), dict)
        self.assertEqual(sequence.size()['main'], number_of_files)
        
    def test_sequence_split_by_echo_time(self):
        sequence = self.app.make_sequence(self.seq_dir)
        sequence.split('InstanceNumber')
        self.assertEqual(type(sequence.split_ds), dict)
        
    def test_sequence_split_into_26_sequences(self):
        sequence = self.app.make_sequence(self.seq_dir)
        sequence.split('InstanceNumber')
        self.assertEqual(len(sequence.split_ds), 26)
        

if __name__ == '__main__':
    ut.main()
