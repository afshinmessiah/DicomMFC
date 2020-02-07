import os, sys, argparse
import numpy
from pydicom.uid import generate_uid
from pydicom.filereader import dcmread
from pydicom.filewriter import dcmwrite
from pydicom.errors import InvalidDicomError

from highdicom.legacy import sop

floating_point_tolerance = 0.00001


class PositionBaseCategoryElement:
    StepSize = 0
    DicomDataset = []

    def AddNewCandidate(self, new_touple):
        success = False
        new_pos = new_touple[1]

        if abs(self.DicomDataset[0][1] - new_pos - self.StepSize) < floating_point_tolerance and \
                new_pos < self.DicomDataset[0][1]:
            success = True
            self.DicomDataset.insert(0, new_touple)
        elif abs(new_pos - self.DicomDataset[-1][1] - self.StepSize) < floating_point_tolerance and \
                new_pos > self.DicomDataset[-1][1]:
            success = True
            self.DicomDataset.append(new_touple)
        return success

    def __init__(self, step: float, ds_pos_elem1: tuple):
        self.StepSize = step
        self.DicomDataset = [ds_pos_elem1]

    def Print(self,Indent=0):
        Prefix=""
        for i in range(0,Indent):
            Prefix += "\t"
        print(Prefix +"========================================================")
        print(Prefix +"step size = {}".format(self.StepSize))
        print(Prefix +"========================================================")
        for el in self.DicomDataset:
            print(Prefix +"---> position {}".format(el[1]))


def GetStudyCategory(ds_list):
    studies = {}
    for ds in ds_list:
        if (ds.StudyInstanceUID in studies):
            studies[ds.StudyInstanceUID].append(ds);
        else:
            studies[ds.StudyInstanceUID] = [ds];
    return studies.items()


def GetSeriesCategory(ds_list):
    series = {}
    for ds in ds_list:
        if (ds.SeriesInstanceUID in series):
            series[ds.SeriesInstanceUID].append(ds);
        else:
            series[ds.SeriesInstanceUID] = [ds];
    return series.items()


def GetSpacingCategory(ds_list):
    series = []
    for ds in ds_list:
        spacing = [ds.PixelSpacing[0], ds.PixelSpacing[1], ds.SliceThickness]
        if len(series) == 0:
            series.append((spacing, [ds]))
        else:
            found_match = False
            for s in series:
                if GetVectorDistance(s[0], ds.PixelSpacing) < floating_point_tolerance:
                    found_match = True
                    s[1].append(ds)
                    break
            if not found_match:
                series.append((spacing, [ds]))
    return series


def GetOrientationCategory(ds_list):
    series = []

    for ds in ds_list:
        orientation = ds.ImageOrientationPatient
        if len(series) == 0:
            series.append((orientation, [ds]))
        else:
            found_match = False
            for s in series:
                if GetVectorDistance(s[0], ds.ImageOrientationPatient) < floating_point_tolerance:
                    found_match = True
                    s[1].append(ds)
                    break
            if not found_match:
                series.append(orientation, [ds])
    return series


def GetVectorDistance(vec1, vec2):
    dist = 0
    for e1, e2 in zip(vec1, vec2):
        d = e1 - e2
        dist += d ** 2
    return numpy.sqrt(dist)


def GetSlicePosition(ds):
    dirr = ds.ImageOrientationPatient

    poss = ds.ImagePositionPatient
    a = numpy.array(dirr[:3])
    b = numpy.array(dirr[3:])
    c = numpy.cross(a, b)
    output = float(c.dot(numpy.array(poss)))
    return output


def ClassifySeriesByPosition(ds_list):
    sorted_ds = []
    ds_pairs = []
    counter = 0

    for ds_element in ds_list:
        ds_pairs.append((ds_element, GetSlicePosition(ds_element)))
    if len(ds_list) == 1:
        return [PositionBaseCategoryElement(1, ds_pairs[0])]

    for sorted_key in sorted(ds_pairs, key=lambda x: x[1]):
        sorted_ds.append(sorted_key)

    category = [PositionBaseCategoryElement(sorted_ds[1][1] - sorted_ds[0][1], sorted_ds[0])]
    for (ds, idx) in zip(sorted_ds[1:], range(1, len(sorted_ds))):
        if not category[-1].AddNewCandidate(ds):
            if idx == len(sorted_ds) - 1:
                category.append(PositionBaseCategoryElement(1, ds))
            else:
                category.append(PositionBaseCategoryElement(sorted_ds[idx + 1][1] - ds[1], ds))

    return category


def HighDicomMultiFrameConvertor(SingleFrameDir, OutputPrefix):
    ModalityCategory = {}
    Files = os.listdir(SingleFrameDir)
    for f in Files:
        try:
            ds = dcmread(os.path.join(SingleFrameDir, f));
        except InvalidDicomError:
            continue
        if ds.Modality in ModalityCategory:
            ModalityCategory[ds.Modality].append(ds);
        else:
            ModalityCategory[ds.Modality] = [ds];
    n = 0
    Output = []
    success = True
    for ModalityName, ModalityDatasets in ModalityCategory.items():
        if ModalityName != 'CT' and ModalityName != 'MR' and ModalityName != 'PET':
            continue
        Modality_Studies = GetStudyCategory(ModalityDatasets)
        for stdy_UID, stdy_ds in Modality_Studies:
            Modality_Series = GetSeriesCategory(stdy_ds)
            for sris_UID, sris_ds in Modality_Series:
                spacing_categories = GetSpacingCategory(sris_ds)
                for spacing_element in spacing_categories:
                    orientation_categories = GetOrientationCategory(spacing_element[1])
                    for orientation_element in orientation_categories:
                        equally_positioned_classes = ClassifySeriesByPosition(orientation_element[1])
                        for uniform_class in equally_positioned_classes:
                            final_ds = []

                            ModalityConvertorClass = getattr(sop, "LegacyConvertedEnhanced" + ModalityName + "Image")
                            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                            print("Distinguish Series ({}):\n\t\tSourceStudyUID:".format(n, stdy_UID) +
                                  "\n\t\tSourceSeriesUID {}\n\t\tPixelSpacing = [{}\t{}\t{}]".
                                  format(sris_UID, spacing_element[0][0], spacing_element[0][1],
                                         spacing_element[0][2]) +
                                  "\n\t\tImageOrientation = \n\t\t\t\t\trow_vector=[{}\t{}\t{}]\n\t\t\t\t\tcol_vector=[{}\t{}\t{}]".
                                  format(orientation_element[0][0], orientation_element[0][1],
                                         orientation_element[0][2],
                                         orientation_element[0][3], orientation_element[0][4],
                                         orientation_element[0][5]))

                            for dds in uniform_class.DicomDataset:
                                final_ds.append(dds[0])
                            uniform_class.Print(3)

                            try:


                                ModalityConvertorObj = ModalityConvertorClass(legacy_datasets=final_ds,
                                                                              series_instance_uid=generate_uid(),
                                                                              series_number=final_ds[0].SeriesNumber,
                                                                              sop_instance_uid=generate_uid(),
                                                                              instance_number=final_ds[
                                                                                  0].InstanceNumber)
                                id = "_%02d_.dcm" % n
                                FileName = os.path.join(OutputPrefix, ModalityName + id)
                                folder = os.path.dirname(FileName)
                                if not os.path.exists(folder):
                                    os.makedirs(folder)

                                dcmwrite(filename=FileName,
                                         dataset=ModalityConvertorObj, write_like_original=True)
                                print("File " + FileName + " was successfully written ...")
                                n = +1
                            except:
                                print(" sth went wrong ...")
                                success = False
                                pass
                            Output.append(success)

    return Output


def main(argv):
    parser = argparse.ArgumentParser(
        description="highdicom MF conversion wrapper. Specify input directory (-i) and output directory (-o).")
    parser.add_argument("-i", "--input-folder", dest="input_folder", metavar="PATH",
                        default="-", required=True, help="Folder of input DICOM files (can contain sub-folders)")
    parser.add_argument("-o", "--output-prefix", dest="output_prefix", metavar="PATH",
                        default=".", required=True, help="File prefix to save converted datasets")
    args = parser.parse_args(argv)

    HighDicomMultiFrameConvertor(args.input_folder, args.output_prefix)


if __name__ == "__main__":
    main(sys.argv[1:])
