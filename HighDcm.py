import os

from pydicom.filereader import dcmread
from pydicom.filewriter import dcmwrite

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


def HighDicomMultiFrameConvertor(SingleFrameDir, OutputPrefix):
    ModalityCategory = {}
    Files = os.listdir(SingleFrameDir)
    for f in Files:
        ds = dcmread(os.path.join(SingleFrameDir, f));
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
        Modality_Studies_Items = Modality_Studies.items();
        for stdy_UID, stdy_ds in Modality_Studies_Items:
            Modality_Series = GetSeriesCategory(stdy_ds).items();
            for sris_UID, sris_ds in Modality_Series:
                ModalityConvertorClass = getattr(sop, "LegacyConvertedEnhanced" + ModalityName + "Image")
                try:
                    ModalityConvertorObj = ModalityConvertorClass(legacy_datasets=sris_ds,
                                                                  series_instance_uid=sris_UID,
                                                                  series_number=sris_ds[0].SeriesNumber,
                                                                  sop_instance_uid=sris_ds[0].SOPInstanceUID,
                                                                  instance_number=sris_ds[0].InstanceNumber)
                    id = "_%02d_.dcm" % n
                    FileName = os.path.join(OutputPrefix, ModalityName+id)
                    dcmwrite(filename=FileName,
                             dataset=ModalityConvertorObj, write_like_original=True)
                    print("File " + id + " was successfully written ...")
                except:
                    print(" sth went wrong ...")
                    success = False
                    pass
    return success
