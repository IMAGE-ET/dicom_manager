#!/usr/bin/python
import os
import sys
import dicom

class DicomDataset(object):
    def __init__(self, dir=''):
        self.main_dir = dir
        self.seq_list = dict()
    

    def ask_for_source_dir(self):
        if len(self.main_dir) == 0:
            self.main_dir = raw_input("Enter path to directory containing DICOM data (drag-and-drop here):").strip().replace('\\', '')
        os.chdir(self.main_dir)


    def get_seq_list(self):
        for root, dirs, files in os.walk(self.main_dir):
            if len(files) != 0:
                for f in files:
                    if open(os.path.join(root, f)).read()[128:132] == 'DICM':
                        continue
                    else:
                        del files[files.index(f)]
            
            if len(files) != 0:
                self.seq_list[root] = files

    def make_sequence(self, root):
        return DicomSequence(root, self.seq_list[root])

class DicomSequence(object):
    
    def __init__(self, root, files):
        self.path = root
        self.files = files
        self.ds = list()
        self.is_split = [False]
        self.split_ds = dict()

        for file in self.files:
            try:
                file_path = os.path.join(self.path, file)
                pydicom_dataset = dicom.read_file(file_path)
                self.ds.append([pydicom_dataset, file_path])
            except dicom.filereader.InvalidDicomError:
                continue

    def __iter__(self):
        for i in [x[0] for x in self.ds]:
            yield i

    def split(self, attribute):
        split_ds = dict()
        known_attribute_values = list()
        for ds in self.ds:
            try:
                attribute_value = getattr(ds[0], attribute) 
                if attribute_value not in known_attribute_values:
                       known_attribute_values.append(attribute_value)
                       split_ds[attribute+'='+str(attribute_value)] = [ds]
                elif attribute_value in known_attribute_values:
                       split_ds[attribute+'='+str(attribute_value)].append(ds)
            except:
                print 'Attribute not found'
                print 'Split failed!'
                break
                return
                
        self.split_ds = split_ds
        self.is_split[0] = True
        self.is_split.append(attribute)
        
    def size(self):
        if not self.is_split[0]:
            return {'main': len(self.ds)}
        elif self.is_split[0]:
            out_size = dict()
            for block in self.split_ds:
                out_size[block] = len(self.split_ds[block])
            return out_size 

    def info(self, attribute = None, tag=[]):    
        if attribute == None and len(tag) == 0:
            print 'Use sequence.info(\'attribute\')'
            print 'Note attribute values are taken from the first file of the sequence\n and may not be the same for all images'
            print 'Here is a list of attributes you can view for this sequence:'
            for i in self.ds[0][0].dir():
                print i        
        elif attribute == None and len(tag) == 2:
            try:
                return self.ds[0][0][tag[0], tag[1]].value
            except:
                print 'Invalid attribute.'
        else:
            try:
                return getattr(self.ds[0][0], attribute)
            except:
                print 'Invalid attribute.'

if __name__ == '__main__':
    app = DicomDataset()
    app.ask_for_source_dir()
    app.get_seq_list()