# this script sorts audio folders in a tree structure like this:
# [a/name_of_composer_starting_from_letter_a/albums...]
# [b/name_of_composer_starting_from_letter_b/albums...]
# [c/name_of_composer_starting_from_letter_c/albums...]
# etc..

import os, shutil

def sort_audiofolders(source: str, target: str) -> None:
    """ move audio folders into correct path in alphabetical structure """

    for composer in os.listdir(source):
        os.chdir(source)
        composer_path = os.path.abspath(composer)
        os.chdir(composer_path)
        for album in os.listdir(composer_path):
            if os.path.isdir(os.path.abspath(album)):
                album_path = os.path.abspath(album)
                dir_path = os.path.dirname(album_path)
                #print(album_path," -- ", dir_path, " -- ", album)
                target_dir = os.path.join(target, composer[0].lower(), composer, album)
                #print(target_dir)
                if os.path.exists(target_dir):
                    print(f"album '{album}' on path '{album_path}' is existing on target path, skipping..")
                    continue
                else:
                    print(f"album '{album}' on path '{album_path}' is not existing on target path '{target_dir}', moving now.. ")
                    shutil.move(album_path, target_dir)
                    
    # TODO log how many folders were moved, how many were skipped (name which was which) 

if __name__ == "__main__":
    source = r"\\192.168.0.109\Public\Music\slsk\!TAGGED"
    target = r"\\192.168.0.109\Public\Music"
    try:
        sort_audiofolders(source, target)
    except Exception as e:
        print(e)