import MFC_Common
import os


# ============================================================================================
def dcm2niixMerge(exe_path, InputFolder, OutputFolder):
    basename = os.path.basename(InputFolder)
    error_file = os.path.join(OutputFolder, basename + "err.txt")
    output_file = os.path.join(OutputFolder, basename + "out.txt")

    command = [exe_path, '-a', 'n', '-c', 'Generated by BWH team',
               '-d', '1',  # directory seearch depth
               '-e', 'n',  # export as nrrd n/y
               '-f', '%p_%t_%s',
               '-o', OutputFolder,
               '--progress', 'y',
               '-v', 'y',
               '-m', 'y',
               '-s', 'n',
               '-w', '1',
               '-z', 'y', InputFolder]

    MFC_Common.run_exe(command, error_file, output_file)


# ================================================================================================
def dcm2niixSingleFile(exe_path, InputFolder, OutputFolder):
    basename = os.path.basename(InputFolder)
    error_file = os.path.join(OutputFolder, basename + "err.txt")
    output_file = os.path.join(OutputFolder, basename + "out.txt")

    command = [exe_path, '-a', 'n', '-c', 'Generated by BWH team',
               '-d', '1',  # directory seearch depth
               '-e', 'n',  # export as nrrd n/y
               '-f', '%b',
               '-o', OutputFolder,
               '--progress', 'y',
               '-v', 'y',
               '-s', 'y',           #single file mode
               '-m','n',            #don't merge
               '-w', '1',
               '-z', 'y', InputFolder]

    MFC_Common.run_exe(command, error_file, output_file)


# exe_path = "E:\\work\\dcm2niix\\bin\\bin\\dcm2niix.exe"
# InputFolder = "E:\\Dropbox\\IDC-MF_DICOM\\data\\TCGA-HNSC\\TCGA-BA-A4IG\\07-28-2002-Outside Read or Comparison PET-87623\\2-PET NAC 2D-75026\\000000.dcm"
# OutputFolder = "E:\\work\\dcm2niix\\bin\\test\\"
# dcm2niix(exe_path, InputFolder, OutputFolder)
