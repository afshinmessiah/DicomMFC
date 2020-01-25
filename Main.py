import os

from pathlib import Path
import time
import shutil
import subprocess
import stat
import xlsxwriter
from HighDcm import HighDicomMultiFrameConvertor
from pydicom.filereader import dcmread
from highdicom.legacy import sop


def recursive_file_find(address, approvedlist):
    filelist = os.listdir(address)
    for filename in filelist:
        fullpath = os.path.join(address, filename);

        if os.path.isdir(fullpath):
            recursive_file_find(fullpath, approvedlist)
            continue;
        filename_size = len(filename);
        if filename.find(".dcm", filename_size - 5) != -1:
            approvedlist.append(fullpath)


# ----------------------------------------------------------------------------------
def recursive_folder_find(address, approvedlist):
    filelist = os.listdir(address)
    has_dicom = bool(0)
    for file_name in filelist:
        fullpath = os.path.join(address, file_name)
        if os.path.isdir(fullpath):
            recursive_folder_find(fullpath, approvedlist)
            continue;
        filename_size = len(file_name)
        if file_name.find(".dcm", filename_size - 5) != -1:
            has_dicom = 1
            break;
    if has_dicom:
        approvedlist.append(address)


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
    PixelMedOutput = InfoPiece()
    PixelMedSuccess = False
    PixelMedVerification = ""
    HighDicomOutput = InfoPiece();
    HighDicomSuccess = False;
    HighDicomVerification = ""


# ---------------------------------------------------------------------
def write_report(seq_, excel_file):
    Fields = {'Input Folder': 0, 'Input File Count': 1,
              'PM Output Folder': 2, 'PM Output File Count': 3,
              'PM Success': 4, 'PM Verification': 5,'HD Output Folder': 6, 'HD Output File Count': 7,
              'HD Success': 8, 'HD Verification':9}

    workbook = xlsxwriter.Workbook(excel_file)
    worksheet = workbook.add_worksheet()
    obj = seq_[0]
    col = 0
    for key, value in Fields.items():
        worksheet.write_string(0, value, key)
    for r in range(1, len(seq_) + 1):
        obj = seq_[r - 1]
        worksheet.write_string(r, Fields['Input Folder'], str(obj.Input.Dir))
        worksheet.write_number(r, Fields['Input File Count'], obj.Input.FileCount)
        worksheet.write_string(r, Fields['PM Output Folder'], str(obj.PixelMedOutput.Dir))
        worksheet.write_number(r, Fields['PM Output File Count'], obj.PixelMedOutput.FileCount)
        worksheet.write_boolean(r, Fields['PM Success'], obj.PixelMedSuccess)
        worksheet.write_string(r, Fields['PM Verification'], obj.PixelMedVerification)
        worksheet.write_string(r, Fields['HD Output Folder'], str(obj.HighDicomOutput.Dir))
        worksheet.write_number(r, Fields['HD Output File Count'], obj.HighDicomOutput.FileCount)
        worksheet.write_boolean(r, Fields['HD Success'], obj.HighDicomSuccess)
        worksheet.write_string(r, Fields['HD Verification'], obj.HighDicomVerification)

    workbook.close()




# =========================================================================
def writ_str_to_text(file_name, content):
    text_file = open(file_name, "w")
    n = text_file.write(content)
    text_file.close()

    # =========================================================================


def run_exe(arg_list, stderr_file, stdout_file):
    print(str(arg_list))
    proc = subprocess.Popen(arg_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # proc.wait(timeout=3600)
    _error = proc.stderr.read();
    writ_str_to_text(stderr_file, _error.decode("ascii"))
    _output = proc.stdout.read();
    writ_str_to_text(stdout_file, _output.decode("ascii"))
    return proc.returncode


# -------------------------------------------------------------------------------------

files = []
# recursive_file_findr(start_dir,files)
#
# for filename in files:
#     print(filename)
start_dir = "E:\\Dropbox\\IDC-MF_DICOM\\data"
# start_dir = "E:\\Dropbox\\IDC-MF_DICOM\\data\\TCGA-UCEC\\TCGA-D1-A2G5\\09-17-1989-Pelvis01PelvisRoutine Adult-16026"
JavaPath = "D:\\ThirdParty\\Java\\jdk-13.0.1\\bin\\java.exe"
save_dir = "E:\\Dropbox\\IDC-MF_DICOM\\output003"
pixelmed_exe = "E:\\work\\pixelmedjavadicom_binaryrelease.20191218"
pixelmed_lib = "E:\\work\\pixelmedjavadicom_dependencyrelease.20191218\\lib"
dcm_verify = "D:\\ThirdParty\\dicom3tools\\dicom3tools_winexe_1.00.snapshot.20191225060430\\dciodvfy.exe"
Excel_report=os.path.join(save_dir,"Report.xlsx")
# p=Path(save_dir)
# p.unlink()
if os.path.exists(save_dir):
    shutil.rmtree(save_dir, onerror=on_rm_error)
folders = []
recursive_folder_find(start_dir, folders)
OutputReport = []
for folder_name in folders:
    print(folder_name)
    info = OutInfo()

    pixelmed_output_folder = (folder_name.replace(start_dir, os.path.join(save_dir,"PixelMed")))
    # pixelmed_output_folder=save_dir+"\\test00"
    if not os.path.exists(pixelmed_output_folder):
        os.makedirs(pixelmed_output_folder)
    save_file_name = os.path.basename(pixelmed_output_folder);
    pathpath = Path(pixelmed_output_folder);
    output_parent = pathpath.parent;
    output_error_file =  pixelmed_output_folder + "_PixelMedError.txt";
    output_stream_file =  pixelmed_output_folder + "_PixelMedOut.txt";

    if not os.path.exists(pixelmed_output_folder):
        os.makedirs(pixelmed_output_folder)

    command = [JavaPath, "-Xmx768m", "-Xms768m","-cp", os.path.join(pixelmed_exe, "pixelmed.jar;")+\
               os.path.join(pixelmed_lib, "additional\\vecmath1.2-1.14.jar"),
               "com.pixelmed.dicom.MultiFrameImageFactory", folder_name, pixelmed_output_folder]


    files = os.listdir(folder_name)
    info.Input.Dir = folder_name
    info.Input.FileCount = len(files)

    exit_code =run_exe(command, output_error_file,output_stream_file)
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


            vr = run_exe([dcm_verify, '-v', final_file_name], final_file_base + "_ver_error.txt"
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
            break;
    #---------------------------------------------------------
    highdicom_output_folder = (folder_name.replace(start_dir, os.path.join(save_dir, "HighDcm")))
    highdicom_output_folder_parent=Path(highdicom_output_folder).parent
    if not os.path.exists(highdicom_output_folder_parent):
        os.makedirs(highdicom_output_folder_parent)
    hd_success=HighDicomMultiFrameConvertor(folder_name,highdicom_output_folder)
    info.HighDicomOutput.Dir = highdicom_output_folder;
    hd_out_files=os.listdir(highdicom_output_folder_parent);
    info.HighDicomOutput.FileCount=len(hd_out_files)
    info.HighDicomSuccess=hd_success
    for hd_out_file in hd_out_files:
        hd_out_file_base=os.path.basename(highdicom_output_folder)
        vr = run_exe([dcm_verify, '-v', os.path.join(highdicom_output_folder_parent,hd_out_file)]
                     , hd_out_file_base + "_ver_error.txt"
                     , hd_out_file_base + "_ver_output.txt")
        if vr :
            info.HighDicomVerification+='0'
        else:
            info.HighDicomVerification += '1'

    OutputReport.append(info)
    write_report(OutputReport, Excel_report)
