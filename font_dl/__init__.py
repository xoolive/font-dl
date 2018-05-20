import os
import os.path

import re
import sys
import base64
import shutil
import urllib

from tools import *

def main():
    if len(sys.argv) < 2:
        print """
    Usage: font-dl <url>

    Parse all resources contained in <url> and download all fonts found.
    It is *your* responsibility to check the license of all files.
        """
        sys.exit(2)

    for topurl in sys.argv[1:]:
        print ("Connecting %s" % topurl)
        result = urllib.urlopen(topurl)
        assert result.getcode() == 200, "Page not found"
        content = parse_content(result.read(), resource_pattern, topurl)

        # Creating a new directory
        dirname = re.search(url_pattern, topurl)
        dirname = dirname.group(2)
        if os.path.isdir(dirname):
            shutil.rmtree(dirname)
        os.mkdir(dirname)

        for doc in content:
            get_font_files(doc['content'], doc['topurl'], dirname)
            decode_fonts(doc['content'], dirname)

        convert_fonts(dirname)

