import glob
import os
from os import walk
from os import listdir
from os.path import isdir, join
import shutil
import re


def handle_mask(folder,songids):
    for musicdb_filepath in glob.glob(os.path.join(folder, "*musicdb*.xml")):
        has_changes = False
        print("    processing",musicdb_filepath)
        fixedfile = ""
        musicdb_filehandle = open(musicdb_filepath,encoding='cp932')
        content = musicdb_filehandle.read()
        result = re.search("<music id=.*?</mask",content, re.DOTALL)
        offset = 0
        while(result is not None):
            #songid
            prefixlen = len("<music id\"")
            songid_end = content[(offset+result.start()+prefixlen+1):(offset+result.start()+prefixlen+20)].index('"')+1
            extract_songid = content[(offset+result.start()+prefixlen+1):(offset+result.start()+prefixlen+songid_end)]
            if extract_songid not in songids:
                #print match as is
                fixedfile += content[(offset):(offset+result.end()+1)]
                offset += result.end()+1
                result = re.search("<music id=.*?</mask",content[offset:], re.DOTALL)
                continue
            print("        processing songid",extract_songid)
            #mask
            prefixlen = len("<mask __type=\"u32\">")
            mask_begin = content[(offset+result.start()):(offset+result.end())].index("<mask __type=\"u32\">")
            mask_end = content[(offset+result.start()+mask_begin+prefixlen+1):(offset+result.start()+mask_begin+prefixlen+50)].index('<')+1
            extract_mask = int(content[(offset+result.start()+mask_begin+prefixlen):(offset+result.start()+mask_begin+prefixlen+mask_end)])
            fixed_mask = extract_mask|0x100
            if extract_mask != fixed_mask:
                print("            fixing mask",extract_mask,"->",fixed_mask)
                newcontent = content[(offset+result.start()+mask_begin+prefixlen):(offset+result.start()+mask_begin+prefixlen+mask_end)].replace(str(extract_mask), str(fixed_mask))
                has_changes = True
                #print match with updated flag
                fixedfile += content[(offset):(offset+result.start()+mask_begin+prefixlen)]
                fixedfile += newcontent
                fixedfile += content[(offset+result.start()+mask_begin+prefixlen+mask_end):(offset+result.end()+1)]
            else:
                print("            mask already includes the load_background flag")
                #print match as is
                fixedfile += content[(offset):(offset+result.end()+1)]
            offset += result.end()+1
            result = re.search("<music id=.*?</mask",content[offset:], re.DOTALL)
        #print rest of file
        fixedfile += content[offset:]
        musicdb_filehandle.close()
        if has_changes:
            print("    Commit changes to file")
            #first make a backup
            newpath = os.path.join("_fix_backgrounds_backup",musicdb_filepath)
            if not os.path.exists(newpath):
                os.makedirs(os.path.join("_fix_backgrounds_backup",folder),exist_ok=True)
                shutil.copyfile(musicdb_filepath, newpath)
            else:
                print("ERROR: a backup already exists for this file, aborting")
                exit(0)
            with open(musicdb_filepath, "w",encoding='cp932',newline='\n') as new_file:
                new_file.write(fixedfile)

bg_diff_path = os.path.join("tex","system","bg_diff_ifs")

folders = []

if os.path.exists(os.path.join("_fix_backgrounds_backup")):
    print("WARNING: a backup path already exists (maybe you run the script already?)")
    input("Press Enter to continue anyways, or Ctrl+C to abort...")

for (dirpath, dirnames, filenames) in walk("."):
    folders.extend(dirnames)
    break

for folder in folders:
    print("Processing",folder,"...")
    prefix_len = len(os.path.join(folder, bg_diff_path))+len("/bg_")
    list = glob.glob(os.path.join(folder, bg_diff_path, "*.ifs"))
    songids = []
    for item in list:
        songid = item[prefix_len:-4]
        songids.append(songid)
    handle_mask(folder,songids)
    print("Done.")

