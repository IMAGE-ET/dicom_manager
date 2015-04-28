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
        
        Note:
            This method will not work on Windows machines due to the backslash
            being the separator.
        
        """
        if len(self.main_dir) == 0:
            question = ("Enter path to directory containing image data"
                       " (drag-and-drop here):")
            self.main_dir = raw_input(question).strip().replace('\\', '')
        os.chdir(self.main_dir)

    def get_seq_list(self):
        """Get paths to image data.
        
        Traverses through main_dir and assignes values to class attributes 
        seq_list and nii_list.
        
        Note:
            DICOM files are identified by the string 'DICM' at offset 128.
            NIFTI files are identified by the string 'n+1', 'nil' at offset 344.
            Gzipped NIFTI files are identified by their extension.
        
        """
        for root, dirs, files in os.walk(self.main_dir):
            dicom_files = list()
            nifti_files = list()
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
    """Wrapper for DICOM files comprising a sequence.
    
    This object gives access to DICOM header information including pixel data. 
    It also stores paths to DICOM files, and calculated image data in some cases.
    It is an iterable object that will yield a pydicom Dataset class instance
    for each slice in a DICOM sequence (i.e. for each DICOM file in files in
    directory root).
    
    Yields:
        pydicom Dataset: one for each slice in DICOM sequence (see above).
    
    Note:
        This object will treat all DICOM files in root as one DICOM sequence.
        If the root folder contains DICOM files from more than one sequence, 
        they will all be treated as one sequence. DICOM file sorting into
        different sequences is not yet implemented.
        
    Args:
        root (str): root directory containing DICOM files.
        files (list): str filenames of DICOM files in root.
        
    Attributes:
        path (str): same as root from Args.
        files (list): same as files from Args.
        ds (list): contains a 2 member list for every slice (every DICOM file).
            ds[0]: instance of pydicom's Dataset class.
            ds[1]: str containing path to DICOM file ds[0] is made from.
            This is done in the __init__ method.
        is_split (bool): list containing True and the name of the attribute the 
            the sequence was split by if the split method was ran (otherwise 
            split[0] = False).
        split_ds (dict): contains output from the split method.
        t2_slices (list): contains a list with with T2 map data stored in numpy
            arrays for each slice. This attribute is assigned its contents
            rather ham-fistedly by the function calculate_T2 in image_math.
    
    """
    
    def __init__(self, root, files):
        self.path = root
        self.files = files
        self.ds = list()
        self.is_split = [False]
        self.split_ds = dict()
        self.t2_slices = list()

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
        """Split the DICOM files into two groups by header attribute.
        
        This method will split ds by the value of a given DICOM header attribute,
        and assign the result to split_ds, a python dictionary. 
        split_ds contains {[str_attribute, str_attribute_value]: list_pydicom_datasets]}.
        This method will also change the value of is_split from [False] to
        [True, attrubute].
        
        Args:
            attribute (str): name of DICOM header attribute. 
        
        """
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
        """Return a representation of the size of the size of the DICOM sequence.
        
        This method will depend on the class attributes is_split, ds, and split_ds.
        
        Note:
            Not used in mv_convert. Will probably be removed.
        
        Returns:
            dict: contains {'main': int_size} if sequence not split, if sequence was
                split then returns {[str_attribute, str_attribute_value]: int_size]}
        
        """
        if not self.is_split[0]:
            return {'main': len(self.ds)}
        elif self.is_split[0]:
            out_size = dict()
            for block in self.split_ds:
                out_size[block] = len(self.split_ds[block])
            return out_size 

    def info(self, attribute = None, tag=[]):
        """Gets information from DICOM header.
        
        Returns header information given the name of the attribute or the DICOM
        header tag id. If invoked without arguments then prints a list of all 
        available attribute names. 
        
        Note:
            This method relies heavily on the pydicom module. Most importantly, 
            it gets the header information from the FIRST FILE in the sequence
            therefore assuming all the DICOM headers in the sequence are identical.
            This is almost never the case.
            
        Args:
            attribute (str, optional): name of attribute to get the value for
            tag (list, optional): a list of two hex ints corresponding to DICOM
                header tag.
        
        Returns:
            Value of DICOM header attributes assigned to tag id or attribute name.
        
        """
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
