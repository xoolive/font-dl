import os
import os.path

import re
import base64
import urllib
import urlparse

# Useful pattern to isolate the name of the website
url_pattern = "(https?.\/\/)?([a-z\d\.-]+\.[a-z\.]{2,6})?([\/\w\s\.-]*)"

# URL to a css file or a json file (may contain @font-face to import)
# often starts with href, but not necessarily
resource_pattern = '=[\"|\']([^\s;]*\.(css|json))'

# A CSS file may import another CSS file
import_pattern = "url\(\"([^\s]*\.css)\""

# The path to a font file (woff, woff2, ttf, or otf)
font_pattern = "([\/\w\s\.-]+)\/([\w\.-]+\.(woff2?|tff|otf))"

# @font-face syntax
# data:[<mediatype>][;base64],<data>
font_face_pattern = "@font-face\s*(\{[^\}]*\})"

font_family_pattern = "font-family\s*:\s*([^;\}]*)(;*)(\}*)"
font_style_pattern = "font-style\s*:\s*([\w\.-]+)\s*(;*)(\}*)"
font_weight_pattern = "font-weight\s*:\s*([\w\.-]+)\s*(;*)(\}*)"

font_base64_pattern = "data:application/x?-?font-(woff2?|ttf|otf).*base64,((?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{4}))"
# font_base64_pattern = "data:font/(opentype).*base64,((?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{4}))"


def parse_content(content, pattern, topurl, acc=[]):
    for i in re.finditer(pattern, content):
        url = urlparse.urljoin(topurl, i.group(1))
        print ("Parsing %s" % url)
        doc = urllib.urlopen(url)
        if doc.getcode() != 200:
            print ("File not accessible: error code %d" % doc.getcode())
            continue
        doc = doc.read()
        acc.append(doc)
        acc = parse_content(doc, import_pattern, topurl, acc)
    return acc

def get_font_files(content, topurl, dirname=os.path.curdir):
    # Iter through all font files found
    for i in re.finditer(font_pattern, content):
        font_url = urlparse.urljoin(topurl, i.group())
        print ("Downloading %s" % font_url)
        urllib.urlretrieve(font_url, os.path.join(dirname, i.group(2)))

def convert_fonts(dirname=os.path.curdir, ext_from=".woff", ext_to=".ttf"):
    import fontforge
    for p in os.listdir(dirname):
        if p[-len(ext_from):] == ext_from:
            try:
                f = fontforge.open(os.path.join(dirname, p))
                print (f.fontname, os.path.join(dirname, p[:-5] + ext_to))
                f.generate(os.path.join(dirname, p[:-5] + ext_to))
            except EnvironmentError:
                print "Converting " + p + " failed"

def decode_fonts(content, dirname = os.path.curdir):
    for i in re.finditer(font_face_pattern, content):
        font_face = i.group()
        font_family = re.search(font_family_pattern, font_face)
        if font_family is not None:
            font_family = font_family.group(1)
            font_family = font_family.strip('\\"\'')
        font_style = re.search(font_style_pattern, font_face)
        if font_style is not None:
            font_style = font_style.group(1)
        font_weight = re.search(font_weight_pattern, font_face)
        if font_weight is not None:
            font_weight = font_weight.group(1)
        if font_family is not None:
            if font_style is not None and font_style != "normal":
                font_family += "-" + font_style
            if font_weight is not None and font_weight != "normal":
                font_family += "-" + font_weight
        b64 = re.search(font_base64_pattern, font_face)
        if b64 is not None:
            font_file_name = font_family + "." + b64.group(1)
            print ("Decoding and writing " + font_file_name)
            f = open(os.path.join(dirname, font_file_name), 'w')
            f.write(base64.b64decode(b64.group(2)))
            f.close()

