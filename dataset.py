#!/usr/bin/python
#! -*- coding: utf-8 -*-

import os
import sys
import dicom

class ImageDataset(object):
    """Holds paths to image data (DICOM or NIFTI).
    
    Attributes:
        main_dir (str): the path to the directory to be searched for images.
        seq_list (dict): contains {str_path_to_root_dir: list_str_dicom_filenames}
        nii_list (dict): contains {str_path_to_root_dir: list_str_nii_filenames}
    """
    def __init__(self, dir=''):
        self.main_dir = dir
        self.seq_list = dict()
        self.nii_list = dict()
        
    def ask_for_source_dir(self):
        """Get a the path to directory containing images.

        Assigns a value to main_dir.        
        """
        if len(self.main_dir) == 0:
            question = ("Enter path to directory containing image data"
                       " (drag-and-drop here):")
            self.main_dir = raw_input(question).strip().replace('\\', '')
        os.chdir(self.main_dir)
        return

    def get_seq_list(self):
        """Get paths to image data.
        
        Traverses through main_dir and assignes values to class attributes 
        seq_list and nii_list.
        
        DICOM files are identified by the string 'DICM' at offset 128.
        NIFTI files are identified by the string 'n+1', 'nil' at offset 344.
        Gzipped NIFTI files are identified by their extension.
        """
        for root, dirs, files in os.walk(self.main_dir):
            dicom_files = []
            nifti_files = []
            if len(files) != 0:
                for f in files:
                    f_data = open(os.path.join(root, f)).read()
                    if f_data[128:132] == 'DICM':
                        dicom_files.append(f)
                    elif f_data[344:347] == 'n+1' or f_data[344:347] == 'ni1':
                        nifti_files.append(f)
                    elif f.endswith('.nii.gz'):
                        nifti_files.append(f)
                    else:
                        continue
            if dicom_files:
                self.seq_list[root] = dicom_files
                
            if nifti_files:
                self.nii_list[root] = nifti_files

    def make_sequence(self, root):
        """Create a DicomSequence given directory containing DICOM files.
        
        Args:
            root (str): directory containing DICOM files (all files must be a 
                part of one DICOM sequence.
                
        Returns:
            DicomSequence object.
        """
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
                sys.exit('Invalid files found. Please clean up dicom directory')

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
                       split_ds[attribute, str(attribute_value)] = [ds]
                elif attribute_value in known_attribute_values:
                       split_ds[attribute, str(attribute_value)].append(ds)
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
            prompt = ("Note attribute values are taken from the first file of the" 
                  " sequence\n and may not be the same for all images")
            print prompt
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
    app = ImageDataset()
    app.ask_for_source_dir()
    app.get_seq_list()
