import itk
import MFC_Common
import numpy as np
import dcm2niix

import sys

floating_point_tolerance = 0.00001


def compareVectors(vec1, vec2, textLabel, Dim=2):
    if type(vec1) is not list:
        v1 = []
        v2 = []
        for i in range(0, Dim):
            v1.append(vec1[i])
            v2.append(vec2[i])
    else:
        v1 = vec1
        v2 = vec2
    diff = MFC_Common.GetVectorDistance(v1, v2)
    if (diff < floating_point_tolerance):
        return ''
    else:
        Message = '{} are not equal.\n\t{} \n\t\tnot equal to \n\t{}'
        return Message.format(textLabel, v1, v2)


def compareImages(imagefile1, imagefile2):
    itk_image = [itk.imread(imagefile1), itk.imread(imagefile2)]

    dim = [itk_image[0].GetImageDimension(), itk_image[1].GetImageDimension()]
    err_mess = compareVectors([dim[0]], [dim[1]], 'Images\' dimensions');
    if len(err_mess) != 0:
        return err_mess

    sz = [itk_image[0].GetLargestPossibleRegion().GetSize(),
          itk_image[1].GetLargestPossibleRegion().GetSize()]
    err_mess = compareVectors(sz[0], sz[1], 'Images\' Size', dim[0]);
    if len(err_mess) != 0:
        return err_mess

    spacings = [itk_image[0].GetSpacing(), itk_image[1].GetSpacing()]
    err_mess = compareVectors(spacings[0], spacings[1], 'Images\' pixel spacing', dim[0]);
    if len(err_mess) != 0:
        return err_mess

    origins = [itk_image[0].GetOrigin(), itk_image[1].GetOrigin()]
    err_mess = compareVectors(origins[0], origins[1], 'Images\' origins', dim[0]);
    if len(err_mess) != 0:
        return err_mess
    directions = [itk_image[0].GetDirection(), itk_image[1].GetDirection()]
    err_mess = compareVectors(directions[0], directions[1], 'Images\' directions', dim[0]);
    if len(err_mess) != 0:
        return err_mess
    return errmess


# itk.ImageFileReader.GetTypes()
# input_filename1 = 'E:\\work\\dcm2niix\\bin\\test\\PET_NAC_2D_20020728124457_2.nii.gz'
# input_filename2 = "E:\\Dropbox\\IDC-MF_DICOM\\output01\\HighDcm\\2-Pelvis Routine  5.0  B40f-80348\\CT_00_.dcm"
# print(compareImages(input_filename1, input_filename2))
# exe_path = "E:\\work\\dcm2niix\\bin\\bin\\dcm2niix.exe"
# InputFolder = "E:\\Dropbox\\IDC-MF_DICOM\\data\\TCGA-HNSC\\TCGA-BA-A4IG\\07-28-2002-Outside Read or Comparison PET-87623\\2-PET NAC 2D-75026\\000000.dcm"
# OutputFolder = "E:\\work\\dcm2niix\\bin\\test\\"
# dcm2niix(exe_path,InputFolder,OutputFolder)