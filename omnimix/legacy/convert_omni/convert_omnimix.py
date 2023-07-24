import glob
import hashlib
import os
import shutil
import sys
import subprocess

import ifstools

from lxml.etree import tostring, fromstring, XMLParser, parse as etree_parse
from lxml.builder import E


def copytree(src, dst, symlinks=False, ignore=None):
    # https://stackoverflow.com/a/13814557
    os.makedirs(dst, exist_ok=True)

    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)

        if os.path.isdir(s):
            copytree(s, d, symlinks, ignore)

        else:
            print("Copying %s to %s..." % (s, d))

            if os.path.exists(d):
                os.unlink(d)

            shutil.copy2(s, d)


def get_unique_files(path, unique_files):
    base_filenames = []

    for filename in unique_files:
        base_filenames.append(os.path.basename(filename))

    for path in glob.glob(os.path.join(path, "*")):
        if os.path.isdir(path):
            return get_unique_files(path, unique_files)

        basename = os.path.basename(path)
        if basename not in base_filenames:
            base_filenames.append(basename)
            unique_files.append(path)

    return unique_files


omnimix_new_patch_path = os.path.join("omnimix_data_install", "omnimix_new", "data_patch")
omnimix_old_patch_path = os.path.join("omnimix_data_install", "omnimix_old", "data_patch")

# Check that the required data is available
assert(os.path.exists("omnimix_data_install") == True)

assert(os.path.exists(os.path.join("omnimix_data_install", "omnimix_old")) == True)
assert(os.path.exists(os.path.join("omnimix_data_install", "omnimix_old", "data")) == True)
assert(os.path.exists(omnimix_old_patch_path) == True)
assert(os.path.exists(os.path.join("omnimix_data_install", "omnimix_old", "db")) == True)

assert(os.path.exists(os.path.join("omnimix_data_install", "omnimix_new")) == True)
assert(os.path.exists(os.path.join("omnimix_data_install", "omnimix_new", "data")) == True)
assert(os.path.exists(omnimix_new_patch_path) == True)
assert(os.path.exists(os.path.join("omnimix_data_install", "omnimix_new", "db")) == True)

# Copy full data folders
for folder in ["omnimix_old", "omnimix_new"]:
    path = os.path.join("omnimix_data_install", folder, "data")

    if os.path.exists(path):
        copytree(path, os.path.join("data_mods", "omnimix"))

# Copy and rename _mod files
data_sets = [
    (os.path.join("data", "tex", "system", "icon_diff.ifs"), "icon_mod", "icon_diff", True),
    (os.path.join("data", "tex", "system", "chara_name_diff.ifs"), "chara_name_mod", "chara_name_diff", True),
    (os.path.join("data", "tex", "system", "chara_name_new_diff.ifs"), "chara_name_new_mod", "chara_name_new_diff", False),
    (os.path.join("data", "tex", "system", "kc_diff.ifs"), "kc_mod", "kc_diff", False),
    (os.path.join("data", "tex", "system", "bg_diff.ifs"), "bg_mod", "bg_diff", False),
    (os.path.join("data", "tex", "system", "ha_merge.ifs"), "ha_mod", "ha_merge", False),
    (os.path.join("data", "tex", "system22", "charapop_diff.ifs"), "charapop_mod", "charapop_diff", False),
]

xml_patch_values = {x[2]: 0 for x in data_sets}

for data_set in data_sets:
    ifs_path, source, target, is_tex_archive = data_set

    print("Processing %s..." % ifs_path)

    tmp_path = os.path.join("tmp", target)
    mod_ifs_path = os.path.join(os.path.dirname(ifs_path), "%s_ifs" % target)
    mod_ifs_path = mod_ifs_path.replace("data", os.path.join("data_mods", "omnimix"))
    os.makedirs(mod_ifs_path, exist_ok=True)
    print("Created ", mod_ifs_path)
	
    if is_tex_archive:
        os.makedirs(os.path.join(mod_ifs_path, "tex"), exist_ok=True)

    if os.path.exists(path):
        copytree(path, os.path.join("data_mods", "omnimix"))
	
    unique_files = []
    unique_files = get_unique_files(os.path.join(omnimix_new_patch_path, source), unique_files)
    unique_files = get_unique_files(os.path.join(omnimix_old_patch_path, source), unique_files)

    # Copy data
    for filename in unique_files:
        target_path = os.path.join(mod_ifs_path, "tex" if is_tex_archive else "", os.path.basename(filename.lower()))

        print("Copying %s to %s" % (filename, target_path))

#        if os.path.exists(target_path):
#            os.unlink(target_path)

        shutil.copy2(filename, target_path)
	
#DEBUG    shutil.rmtree(tmp_path)

# Copy db files
output_db_path = os.path.join("data_mods", "omnimix")

db_paths = [
    os.path.join("omnimix_data_install", "omnimix_old", "db"),
    os.path.join("omnimix_data_install", "omnimix_new", "db"),
]

db_filenames = []
for path in db_paths:
    if not os.path.exists(path):
        continue

    for filename in sorted(glob.glob(os.path.join(path, "*.xml"))):
        if filename not in db_filenames:
            db_filenames.append(filename)

    copytree(path, output_db_path)

# Cleanup tmp folder since it's no longer needed
#shutil.rmtree("tmp")

print("Done!")
