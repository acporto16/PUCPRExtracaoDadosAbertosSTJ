import os
import re

# Em C:/_PUCPR/PrjDadosAbertos/lib.py
def ensure_dir_exists(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

removeCRLF = lambda field:( re.sub(r'[\r\n\t]', '', field[0]) if field else '' )

removeCRLFString = lambda field:( re.sub(r'[\r\n\t]', '', field) if field else '' )