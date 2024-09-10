# DONT USE THIS , THIS IS A TOOL TO DELETE EVERYTHING

LOCAL_STORAGE_PATHS  =  ["static/mediaSource/nsfw"]
STORAGE_FILE_PATH = ["game-data.json"]

import os

trash_bin = list()
for path in LOCAL_STORAGE_PATHS:
    items = os.listdir(path)
    
    for item in items:
        trash_bin.append(os.path.join(path,item))


def destroyer(file_path) -> None:
    if os.path.isfile(file_path):
        os.remove(file_path)

with open(STORAGE_FILE_PATH,'w') as file:
    file.write(r'{"MEGA_TAG_LIST": [],"NSFW": []}')