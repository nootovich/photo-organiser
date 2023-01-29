# [ ] Move all files to a temporary folder except for the ones with same names
#
# [ ] Give a promt ot the user with all the files and options:
# [ ] A) if they are the same:
#       1) choose which one to keep, and delete the rest;
#       2) choose to keep all, and rename all except for one as copies;
#       3) choose which one to keep, which to rename, and which to delete;
#       4) choose to delete all (with a warning);
# [ ] B) if they are different:
#       1) choose to keep all, add their differences to names and rename copies;
#       2) choose to keep only unique ones and add their differences to names;
#       3) choose which one to keep, which to rename, and which to delete;
#       4) choose to delete all (with a warning);
#
# [ ] Save info about moved files (for general restoring purposes)


import os, sys, shutil, hashlib

WORKING_DIR = 'D:' + os.sep + 'photo organiser'
INFO_FILE   =        os.sep + 'info.txt'

INPUT_PATH   = WORKING_DIR + os.sep + 'input'
OUTPUT_PATH  = WORKING_DIR + os.sep + 'output'
BACKUP_PATH  = WORKING_DIR + os.sep + 'Photo dump test (orig)'
IMAGES_PATH  = OUTPUT_PATH + os.sep + 'images'
COPIES_PATH  = OUTPUT_PATH + os.sep + 'copies'

DELETED = '[DELETED]'
UNKNOWN = '[UNKNOWN]'

arg_input_dirs    = []
arg_output_dir    = ""
arg_info_location = ""
arg_delete_copies = False

info = []
dir_info_start = 0
# TODO: maybe rename 'info'?

class File:
    dir : str # absolute path
    name: str
    hash: str 

    def __init__(self, dir: str, name: str) -> None:
        self.dir  = dir
        self.name = name
        with open(get_filepath(self), 'rb') as f:
            self.hash = hashlib.file_digest(f, "sha256").hexdigest()

class FilePtr:
    dir : str
    name: str

    def __init__(self, dir: str, name: str) -> None:
        self.dir  = dir
        self.name = name

def print_usage() -> None:
    print("[INFO]: Usage:\n" +
    "\tphoto_organiser.py [-d] [-i input_dirs] [-o output_dir] [-l log_location]\n" 
    "\t-d\tDelete duplicates of files\t\t\t\t(default: keep)\n" +
    "\t-i\tSpecify input directories (separated by commas)\t\t(default: <./>)\n" +
    "\t\t\texample: -i \"<dir1, dir2, ..., dirN>\"\n" +
    "\t-o\tSpecify output directory\t\t\t\t(default: <./output>)")

def parse_arguments() -> None:
    global arg_input_dirs, arg_output_dir, arg_info_location, arg_delete_copies
    input_provided, output_provided = False, False
    try:
        for i in range(1, len(sys.argv)):
            arg = sys.argv[i]
            arg_delete_copies = arg == '-d'
            
            if arg == '-i':
                input_provided = True
                for dir in sys.argv[i+1].split(','):
                    arg_input_dirs.append(dir.strip())
                i += 1
            
            if arg == '-o':
                output_provided = True
                arg_output_dir = sys.argv[i+1]
                i += 1
            
            if arg == '-l':
                arg_info_location = sys.argv[i+1]    
    except:
        print("[ERROR]: Couldn't parse arguments for some reason", file=sys.stderr)
        print_usage()
        exit(1)
    
    if input_provided and output_provided:
        return
    if not input_provided:
        print("[ERROR]: Input folder(s) not provided", file=sys.stderr)
        print_usage()
    if not output_provided:
        print("[ERROR]: Output folder not provided", file=sys.stderr)
        print_usage()
    exit(1)

def init_testing_dirs() -> None:
    try:
        shutil.  rmtree( INPUT_PATH, True)
        shutil.  rmtree(OUTPUT_PATH, True)
        shutil.copytree(BACKUP_PATH, INPUT_PATH)
        os.chdir( INPUT_PATH)
        os.mkdir(OUTPUT_PATH)
    except:
        print("[ERROR]: Couldn't initialise folders for some reason")
        exit(1)
      
def get_filepath(file: File | FilePtr) -> str:
    return os.sep + file.name if file.dir == None else file.dir + os.sep + file.name

def get_rel_dir(file: File | FilePtr, parent_path: str) -> str:
    return parent_path if file.dir == None else file.dir.removeprefix(parent_path)

def get_rel_filepath(file: File | FilePtr, parent_path: str) -> str:
    return os.sep + file.name if file.dir == None else file.dir.removeprefix(parent_path) + os.sep + file.name

def get_extension(file_name: str) -> str:
    tokens = file_name.split('.')
    return tokens[len(tokens)-1] if len(tokens) > 1 else None

def is_image(file_name: str) -> bool:
    extension = get_extension(file_name)
    if extension == None:
        return False
    
    ext = extension.lower()
    return ext == "png" or ext == "jpg" or ext == "jpeg"

def mkdir(dir: str) -> bool:
    try:
        os.mkdir(dir)
        return True
    except:
        return False

def copy_file(source: File | FilePtr, target: File | FilePtr) -> None:
    assert len(source.dir ) > 0, '[ERROR]: The source directory should be provided'
    assert len(target.dir ) > 0, '[ERROR]: The target directory should be provided'
    assert len(source.name) > 0, '[ERROR]: The source name' + ' should be provided'
    assert len(target.name) > 0, '[ERROR]: The target name' + ' should be provided'
    mkdir(target.dir)
    try:
        shutil.copyfile(get_filepath(source), get_filepath(target))
        info.append((source, target))
    except:
        print(f"[ERROR]: Couldn't move file '{get_filepath(source)}' to '{get_filepath(target)}'")
        exit(1)

def recursive_get_dir_images(dir: str):
    result = []
    for (directory, _, files) in os.walk(dir):
        for file in files:
            if is_image(file): result.append(File(directory, file))
    return result

def recursive_print_dir_images(dir: str) -> None:
    images = recursive_get_dir_images(dir)
    for img in images:
        print(f"[INFO]: Found image '{img.name}' inside '{img.dir}'")

def save_info(dir: str, input_dir: str) -> None:
    global info, dir_info_start
    info_contents = f"\nINPUT_DIR: {input_dir}\nOUTPUT_DIR: {arg_output_dir}\n"
    with open(dir + INFO_FILE, 'a', encoding="utf-8") as info_file:
        for i in range(dir_info_start, len(info)):
            info_file_tuple = info[i]
            input_file      = info_file_tuple[0]
            output_file_ptr = info_file_tuple[1]
            info_contents += f"{input_file.hash}: {get_rel_filepath(input_file, input_dir)} -> {get_rel_filepath(output_file_ptr, arg_output_dir)}\n"
        try:
            info_file.write(info_contents)
            print(f"[INFO]: Successfully saved info as '{info_file.name}'")
        except:
            print( "[INFO]: "+f"Failed to save info as '{info_file.name}'")
    dir_info_start = len(info)

def get_dir_info(dir: str) -> str:
    try:
        return open(dir + INFO_FILE, 'r', encoding="utf-8").read()
    except:
        return UNKNOWN
    
def find_copies(file: File, source_dir: str) -> int:
    copies_counter = 0
    for info_entry in info:
        source = info_entry[0] # first element is the source file in the entry 
        # TODO: refactor 'info' to be a named tuple or smth like that
        # so that you can actually see what is stored in 'info'
        if file.hash == source.hash:
            print(f"[INFO]: '{get_rel_filepath(file, source_dir)}' is a copy of '{get_rel_filepath(source, source_dir)}'")
            copies_counter += 1
    return copies_counter

def process_files(input_dirs: tuple):
    for input_dir in input_dirs:
        images = recursive_get_dir_images(input_dir)
        
        for img in images:
            copies_counter = find_copies(img, input_dir)
            
            if copies_counter > 0:
                if arg_delete_copies: info.append((img, FilePtr("", DELETED)))
                else: copy_file(img, FilePtr(arg_output_dir, img.name[:-4] + f'_copy({copies_counter})' + img.name[-4:]))
            else: copy_file(    img, FilePtr(arg_output_dir, img.name))
        
        save_info(arg_info_location, input_dir)
        print(f"[INFO]: Info file contents:\n'{get_dir_info(arg_info_location)}'")    

def __init__() -> None:   
    global arg_input_dirs, arg_output_dir, arg_info_location, arg_delete_copies
    parse_arguments()
    init_testing_dirs()
    arg_info_location = OUTPUT_PATH # TODO: temporary
    process_files(arg_input_dirs)

if __name__ == "__main__":
    __init__()
