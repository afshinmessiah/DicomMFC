import os, sys, argparse

from pydicom.filereader import dcmread
from pydicom.filewriter import dcmwrite
from pydicom.errors import InvalidDicomError

from highdicom.legacy import sop


def GetStudyCategory(ds_list):
    studies = {}
    for ds in ds_list:
        if (ds.StudyInstanceUID in studies):
            studies[ds.StudyInstanceUID].append(ds);
        else:
            studies[ds.StudyInstanceUID] = [ds];
    return studies


def GetSeriesCategory(ds_list):
    series = {}
    for ds in ds_list:
        if (ds.SeriesInstanceUID in series):
            series[ds.SeriesInstanceUID].append(ds);
        else:
            series[ds.SeriesInstanceUID] = [ds];
    return series
def GetSOPCategory(ds_list):
    series = {}
    for ds in ds_list:
        if (ds.SOPInstanceUID in series):
            series[ds.SOPInstanceUID].append(ds);
        else:
            series[ds.SOPInstanceUID] = [ds];
    return series

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
    success = True
    for ModalityName, ModalityDatasets in ModalityCategory.items():
        if ModalityName != 'CT' and ModalityName != 'MR' and ModalityName != 'PET':
            continue
        Modality_Studies = GetStudyCategory(ModalityDatasets)
        Modality_Studies_Items = Modality_Studies.items()
        for stdy_UID, stdy_ds in Modality_Studies_Items:
            Modality_Series = GetSeriesCategory(stdy_ds)
            Modality_Series_Items = GetSeriesCategory(stdy_ds).items()
            for sris_UID, sris_ds in Modality_Series_Items:
                ModalityConvertorClass = getattr(sop, "LegacyConvertedEnhanced" + ModalityName + "Image")
                sops=GetSOPCategory(sris_ds)
                sorted_ds=[]
                for sorted_key in sorted(sops.items(),key=lambda x: x[1][0].InstanceNumber):
                    sorted_ds.append(sorted_key[1][0])
                    print("{}---->{}".format(sorted_key[0],sorted_key[1][0].InstanceNumber))
                    print("AccessionNumb---->{}".format( sorted_key[1][0].AccessionNumber))

                try:
                    ModalityConvertorObj = ModalityConvertorClass(legacy_datasets=sorted_ds,
                                                                  series_instance_uid=sris_UID,
                                                                  series_number=sorted_ds[0].SeriesNumber,
                                                                  sop_instance_uid=sorted_ds[0].SOPInstanceUID,
                                                                  instance_number=sorted_ds[0].InstanceNumber)
                    id = "_%02d_.dcm" % n
                    FileName = os.path.join(OutputPrefix, ModalityName+id)
                    folder = os.path.dirname(FileName)
                    if not os.path.exists(folder):
                        os.makedirs(folder)

                    dcmwrite(filename=FileName,
                             dataset=ModalityConvertorObj, write_like_original=True)
                    print("File " + id + " was successfully written ...")
                except:
                    print(" sth went wrong ...")
                    success = False
                    pass
    return success

def main(argv):
    parser = argparse.ArgumentParser(description="highdicom MF conversion wrapper. Specify input directory (-i) and output directory (-o).")
    parser.add_argument("-i", "--input-folder", dest="input_folder", metavar="PATH",
                        default="-", required=True, help="Folder of input DICOM files (can contain sub-folders)")
    parser.add_argument("-o", "--output-prefix", dest="output_prefix", metavar="PATH",
                        default=".", required=True, help="File prefix to save converted datasets")
    args = parser.parse_args(argv)

    HighDicomMultiFrameConvertor(args.input_folder, args.output_prefix)

if __name__ == "__main__":
  main(sys.argv[1:])
