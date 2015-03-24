#!/usr/bin/python
import os
import unittest as ut

from dataset import DicomDataset

home_folder = os.path.dirname(os.getcwd())+'/test_dicom'
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
        self.assertEqual(number_of_files, 50)
        
    def test_sequence_items_are_pydicom_datasets(self):
        sequence = self.app.make_sequence(self.seq_dir)
        self.assertEqual(sequence.info('PatientID'), str(1625))
        self.assertEqual(sequence.info(tag=[0x10, 0x10]), str(1625))
        
    def test_sequence_size_method(self):
        sequence = self.app.make_sequence(self.seq_dir)
        number_of_files = len(self.app.seq_list[test_sequence])
        self.assertIsInstance(sequence.size(), dict)
        self.assertEqual(sequence.size()['main'], number_of_files)
        
    def test_sequence_split_by_echo_time(self):
        sequence = self.app.make_sequence(self.seq_dir)
        sequence.split('EchoTime')
        self.assertEqual(type(sequence.split_ds), dict)
        
    def test_sequence_split_into_two_25_slice_sequences(self):
        sequence = self.app.make_sequence(self.seq_dir)
        sequence.split('EchoTime')
        size_22 = len(sequence.split_ds['EchoTime=22'])
        size_90 = len(sequence.split_ds['EchoTime=90'])
        self.assertEqual(size_22, 25)
        self.assertEqual(size_90, 25)
        self.assertEqual(len(sequence.ds), size_22 + size_90)
        

if __name__ == '__main__':
    ut.main()