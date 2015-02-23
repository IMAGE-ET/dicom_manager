#!/usr/bin/python
import os
import sys
import dicom

class DicomDataset(object):
    def __init__(self, dir=''):
        self.main_dir = dir
        self.seq_list = dict()
    
    resource_dir = os.path.dirname(os.path.realpath(__file__))+'/resources'

    def ask_for_source_dir(self):
        if len(self.main_dir) == 0:
            self.main_dir = raw_input("Enter path to directory containing DICOM data (drag-and-drop here):").strip().replace('\\', '')
        os.chdir(self.main_dir)


    def get_seq_list(self):
        for root, dirs, files in os.walk(self.main_dir):
            if len(files) != 0:
                for f in files:
                    try:
                        if open(f).read()[128:132] == 'DICM':
                            continue
                        else:
                            del files[files.index(f)]
                    except:
                        del files[files.index(f)]
            if len(files) != 0:
                self.seq_list[root] = files

    def make_sequence(self, root):
        return DicomSequence(root, self.seq_list[root])

class DicomSequence(object):
    
    def __init__(self, root, files):
        self.path = root
        self.files = files
        self.sequence = list()

        for file in self.files:
            try:
                pydicom_dataset = dicom.read_file(os.path.join(self.path, file), stop_before_pixels=True)
                self.sequence.append(pydicom_dataset)
            except dicom.filereader.InvalidDicomError:
                continue
        
    def info(self, attribute = None):    
        if attribute == None:
            print 'Use sequence.info(\'attribute\')'
            print 'Note attribute values are taken from the first file of the sequence\n and may not be the same for all images'
            print 'Here is a list of attributes you can view for this sequence:'
            for i in self.sequence[0].dir():
                print i 
        else:
            try:
                return getattr(self.sequence[0], attribute)
            except:
                print 'Attribute not found.'

if __name__ == '__main__':
    app = ConverterApp()
    app.ask_for_source_dir()
    app.get_seq_list()
