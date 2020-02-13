import os
import subprocess
import numpy
def GetVectorDistance(vec1, vec2):
    dist = 0
    for e1, e2 in zip(vec1, vec2):
        d = e1 - e2
        dist += d ** 2
    return numpy.sqrt(dist)



# =========================================================================
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


# =========================================================================---
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


# =========================================================================
def write_str_to_text(file_name, content):
    text_file = open(file_name, "w")
    n = text_file.write(content)
    text_file.close()


# =========================================================================


def run_exe(arg_list, stderr_file, stdout_file):
    # print(str(arg_list))
    out_text = ""
    for a in arg_list:
        has_ws = False
        for ch in a:
            if ch.isspace():
                has_ws = True
                break
        if has_ws:
            out_text += "\"{}\" ".format(a)
        else:
            out_text += "{} ".format(a)
    print(out_text)

    proc = subprocess.run(arg_list,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # try:
    #     outs, errs = proc.communicate(timeout=5)
    # except subprocess.TimeoutExpired:
    #     proc.kill()
    #     outs, errs = proc.communicate()
    _error = proc.stderr
    write_str_to_text(stderr_file, _error.decode("ascii"))
    _output = proc.stdout
    write_str_to_text(stdout_file, _output.decode("ascii"))
    return proc.returncode
