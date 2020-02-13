import os

from pathlib import Path
import time
import shutil
import subprocess
import stat
import xlsxwriter
from HighDcm import HighDicomMultiFrameConvertor
import MFC_Common
import itkImageVerification
import dcm2niix


# -----------------------------------------------------------------------------------------
def on_rm_error(func, path, exc_info):
    # path contains the path of the file that couldn't be removed
    # let's just assume that it's read-only and unlink it.
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)


# ---------------------------------------------------------------------------------------
class InfoPiece:
    def __init__(self, dir_='', filecount_=0):
        self.Dir = dir_
        self.FileCount = filecount_

    Dir = ''
    FileCount = 0


# -------------------------------------------------------------------------------------
class OutInfo:
    def __init__(self):
        self.Input = InfoPiece()
        self.PixelMedOutput = InfoPiece()
        self.PixelMedSuccess = False
        self.HighDicomOutput = InfoPiece();
        self.HighDicomSuccess = False;

    Input = InfoPiece()
    InputVerification = ""
    PixelMedOutput = InfoPiece()
    PixelMedSuccess = False
    PixelMedVerification = ""
    HighDicomOutput = InfoPiece()
    HighDicomSuccess = False;
    HighDicomVerification = ""
# ---------------------------------------------------------------------
def write_niix_report(seq_, excel_file):


    workbook = xlsxwriter.Workbook(excel_file)
    worksheet = workbook.add_worksheet()
    obj = seq_[0]
    col = 0
    worksheet.write_string(0, 0, 'Input File1')
    worksheet.write_string(0, 1, 'Input File2')
    worksheet.write_string(0, 2, 'err message')
    for (data, r) in zip(seq_, range(1,len(seq_)+1)):
        worksheet.write_string(r, 0, data[0])
        worksheet.write_string(r, 1, data[1])
        worksheet.write_string(r, 2, data[2])


    workbook.close()


# ---------------------------------------------------------------------
def write_report(seq_, excel_file):
    Fields = ('Input Folder', 'Input File Count', 'Input Verification',
              'PM Output Folder', 'PM Output File Count',
              'PM Success', 'PM Verification', 'HD Output Folder', 'HD Output File Count',
              'HD Success', 'HD Verification')

    workbook = xlsxwriter.Workbook(excel_file)
    worksheet = workbook.add_worksheet()
    obj = seq_[0]
    col = 0
    for value, idx in zip(Fields, range(0, len(Fields))):
        worksheet.write_string(0, idx, value)
    for r in range(1, len(seq_) + 1):
        obj = seq_[r - 1]
        worksheet.write_string(r, Fields.index('Input Folder'), str(obj.Input.Dir))
        worksheet.write_number(r, Fields.index('Input File Count'), obj.Input.FileCount)
        worksheet.write_string(r, Fields.index('Input Verification'), obj.InputVerification)
        worksheet.write_string(r, Fields.index('PM Output Folder'), str(obj.PixelMedOutput.Dir))
        worksheet.write_number(r, Fields.index('PM Output File Count'), obj.PixelMedOutput.FileCount)
        worksheet.write_boolean(r, Fields.index('PM Success'), obj.PixelMedSuccess)
        worksheet.write_string(r, Fields.index('PM Verification'), obj.PixelMedVerification)
        worksheet.write_string(r, Fields.index('HD Output Folder'), str(obj.HighDicomOutput.Dir))
        worksheet.write_number(r, Fields.index('HD Output File Count'), obj.HighDicomOutput.FileCount)
        worksheet.write_boolean(r, Fields.index('HD Success'), obj.HighDicomSuccess)
        worksheet.write_string(r, Fields.index('HD Verification'), obj.HighDicomVerification)

    workbook.close()


files = []
# recursive_file_findr(start_dir,files)
#
# for filename in files:
#     print(filename)
start_dir = "E:\\Dropbox\\IDC-MF_DICOM\\data"
start_dir = "E:\\Dropbox\\IDC-MF_DICOM\\data\\TCGA-UCEC\\TCGA-D1-A2G5\\09-17-1989-Pelvis01PelvisRoutine Adult-16026"
JavaPath = "D:\\ThirdParty\\Java\\jdk-13.0.1\\bin\\java.exe"
save_dir = "E:\\Dropbox\\IDC-MF_DICOM\\output01"
pixelmed_exe = "E:\\work\\pixelmedjavadicom_binaryrelease.20191218"
pixelmed_lib = "E:\\work\\pixelmedjavadicom_dependencyrelease.20191218\\lib"
dcm_verify = "D:\\ThirdParty\\dicom3tools\\dicom3tools_winexe_1.00.snapshot.20191225060430\\dciodvfy.exe"
Excel_report = os.path.join(save_dir, "Report.xlsx")
niix_excel_file = os.path.join(save_dir, "NiixReport.xlsx")
# p=Path(save_dir)
# p.unlink()
if os.path.exists(save_dir):
    shutil.rmtree(save_dir, onerror=on_rm_error)
folders = []
MFC_Common.recursive_folder_find(start_dir, folders)
OutputReport = []
niix_ver_errs=[]
for folder_name in folders:
    print(folder_name)
    info = OutInfo()

    pixelmed_output_folder = (folder_name.replace(start_dir, os.path.join(save_dir, "PixelMed")))
    # pixelmed_output_folder=save_dir+"\\test00"
    if not os.path.exists(pixelmed_output_folder):
        os.makedirs(pixelmed_output_folder)
    save_file_name = os.path.basename(pixelmed_output_folder);
    pathpath = Path(pixelmed_output_folder);
    output_parent = pathpath.parent;
    output_error_file = pixelmed_output_folder + "_PixelMedError.txt";
    output_stream_file = pixelmed_output_folder + "_PixelMedOut.txt";

    if not os.path.exists(pixelmed_output_folder):
        os.makedirs(pixelmed_output_folder)

    command = [JavaPath, "-Xmx768m", "-Xms768m", "-cp", os.path.join(pixelmed_exe, "pixelmed.jar;") + \
               os.path.join(pixelmed_lib, "additional\\vecmath1.2-1.14.jar"),
               "com.pixelmed.dicom.MultiFrameImageFactory", folder_name, pixelmed_output_folder]

    files = os.listdir(folder_name)
    info.Input.Dir = folder_name
    info.Input.FileCount = len(files)
    input_check_folder = (folder_name.replace(start_dir, os.path.join(save_dir, "inputcheck")))
    if not os.path.exists(input_check_folder):
        os.makedirs(input_check_folder)
    for file in files:
        infilepath = os.path.join(folder_name, file)
        vr = MFC_Common.run_exe([dcm_verify, '-filename', infilepath]
                                , os.path.join(input_check_folder, file + "_ver_error.txt")
                                , os.path.join(input_check_folder, file + "_ver_output.txt"))
        if vr == 0:
            info.InputVerification += '1'
        else:
            info.InputVerification += '0'

    exit_code = MFC_Common.run_exe(command, output_error_file, output_stream_file)
    if exit_code == 0:
        info.PixelMedSuccess = True;
    else:
        info.PixelMedSuccess = False;

    output_files = os.listdir(pixelmed_output_folder)
    info.PixelMedOutput.Dir = output_parent;
    info.PixelMedOutput.FileCount = len(output_files)

    i = 0
    for f in output_files:
        f_size = len(f);
        full_f = os.path.join(pixelmed_output_folder, f);
        if os.path.isfile(full_f) and (f.find(".", 3) != -1):
            id = "_%02d_" % i
            final_file_base = pixelmed_output_folder + id
            final_file_name = final_file_base + ".dcm"
            print("renameing " + full_f + " to " + final_file_name)
            if os.path.exists(final_file_name):
                os.remove(final_file_name)
            os.rename(full_f, final_file_name)

            vr = MFC_Common.run_exe([dcm_verify, '-filename', final_file_name], final_file_base + "_ver_error.txt"
                                    , final_file_base + "_ver_output.txt")
            if vr == 0:
                info.PixelMedVerification += "1"
            else:
                info.PixelMedVerification += "0"

            i += 1
    while 1:
        try:
            shutil.rmtree(pixelmed_output_folder)
        except:
            print("Something went wrong ... try again")
            time.sleep(5)
        else:
            break
    # ---------------------------------------------------------
    highdicom_output_folder = (folder_name.replace(start_dir, os.path.join(save_dir, "HighDcm")))
    highdicom_output_folder_parent = Path(highdicom_output_folder).parent
    if not os.path.exists(highdicom_output_folder_parent):
        os.makedirs(highdicom_output_folder_parent)
    hd_success = HighDicomMultiFrameConvertor(folder_name, highdicom_output_folder)
    info.HighDicomOutput.Dir = highdicom_output_folder;
    hd_out_files = os.listdir(highdicom_output_folder)
    hd_dcm_files = []
    for ffiles in hd_out_files:
        if ffiles.endswith(".dcm"):
            hd_dcm_files.append(ffiles)
    info.HighDicomOutput.FileCount = len(hd_dcm_files)
    info.HighDicomSuccess = hd_success
    for hd_dcm_file in hd_dcm_files:
        hd_out_file_base = os.path.basename(hd_dcm_file)
        vr = MFC_Common.run_exe([dcm_verify, '-filename', os.path.join(highdicom_output_folder, hd_dcm_file)]
                                , os.path.join(highdicom_output_folder, hd_out_file_base + "_ver_error.txt")
                                , os.path.join(highdicom_output_folder, hd_out_file_base + "_ver_output.txt"))
        if vr == 0:
            info.HighDicomVerification += '1'
        else:
            info.HighDicomVerification += '0'

    OutputReport.append(info)
    write_report(OutputReport, Excel_report)
    # ------------------------------------------------------------------------------------

    exe_path = "E:\\work\\dcm2niix\\bin\\bin\\dcm2niix.exe"
    input_files = os.listdir(folder_name)
    niix_output_folder = (folder_name.replace(start_dir, os.path.join(save_dir, "niix")))
    if not os.path.exists(niix_output_folder):
        os.makedirs(niix_output_folder)
    for file in input_files:
        input_file = os.path.join(folder_name, file)
        dcm2niix.dcm2niixSingleFile(exe_path, input_file, niix_output_folder)
        niix_output_file = os.path.join(niix_output_folder, file + ".nii.gz")
        err = itkImageVerification.compareImages(input_file, niix_output_file)

        if len(err) > 0:
            niix_ver_errs.append((input_file, niix_output_file, err))
    write_niix_report(niix_ver_errs, niix_excel_file)

