import unittest as ut
from dataset import DicomDataset

home_folder = None
test_sequence = None
class DicomDatasetTest(ut.TestCase):

    def setUp(self):
        self.app = DicomDataset(home_folder)
        self.app.get_seq_list()
        self.seq_dir = test_sequence
    
    def test_converter_assigns_main_dir_correctly(self):
        self.assertEqual(self.app.main_dir, home_folder)
        
    def test_converter_seq_list_not_empty(self):
        self.assertFalse(len(self.app.seq_list) == 0)
        
    def test_sequence_items_are_pydicom_datasets(self):
        sequence = self.app.make_sequence(self.seq_dir)
        self.assertEqual(sequence.info('PatientID'), str(1625))
        
    def test_sequence_split_by_echo_time_works(self):
    	sequence = self.app.make_sequence(self.seq_dir)
    	print type(sequence)
    	sequence.split('EchoTime')
    	self.assertEqual(len(sequence), 2)

if __name__ == '__main__':
    ut.main()
