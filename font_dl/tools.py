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
# TODO match //use.typekit.net/ugs0xsx.js
resource_pattern = '=[\"|\']([^\s;]*\.(css|json|typekit)[^\s]*)[\"|\']'

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

font_base64_pattern = "data:(application/x?-?font-|font/)(opentype|woff2?|ttf|otf).*base64,((?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{4}))"


## TODO
# - (**) Relative path from current CSS resource (may be different topurl!)
#        https://fast.fonts.net/cssapi/7492f661-79f4-4ab2-90f2-6a9eaf984a75.css
#        debug http://minutebutterfly.com/true-https/
# - ( )  all kinds of @import -> see google fonts, fonts.com
# - (*)  <link type="text/css" href="http://fonts.googleapis.com/css?family=Oswald:400,300"/>
# - (*)  main("*.css")
# - (*)  data:font/
# - ( )  https://typ.io/fonts/garamond_premier
# <link href="http://use.typekit.net/c/1f1e76/1w;alternate-gothic-no-1-d,2,TV3:M:n4;futura-pt,2,SHC:M:n8;garamond-premier-pro,2,XtF:M:i4,XtJ:M:n4;proxima-nova,2,W0V:M:n4,W0Y:M:n7/d?3bb2a6e53c9684ffdc9a9afe1f5b2a62e5d76b099c828680e711f4226e668697f12af063e70c6c6d752b3779675ea7b345c15865538faf9e65fa0039db783979fbe782fe178a4130d9b10461c5b567dab6b549fbf6" rel="stylesheet">
# <link rel="stylesheet" id="cb-font-stylesheet-css" href="//fonts.googleapis.com/css?family=Montserrat%3A400%2C700%7COpen+Sans%3A400%2C700%2C400italic&amp;ver=2.0.2" type="text/css" media="all">

def parse_content(content, pattern, topurl, acc=[]):
    for i in re.finditer(pattern, content):
        url = urlparse.urljoin(topurl, i.group(1))
        print ("Parsing %s" % url)
        doc = urllib.urlopen(url)
        if doc.getcode() != 200:
            print ("File not accessible: error code %d" % doc.getcode())
            continue
        doc = doc.read()
        acc.append({'content' : doc, 'topurl' : url})
        acc = parse_content(doc, import_pattern, url, acc)
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
            extension = b64.group(2)
            if extension == "opentype":  # weird...
                extension = "woff"
            font_file_name = font_family + "." + extension
            print ("Decoding and writing " + font_file_name)
            f = open(os.path.join(dirname, font_file_name), 'w')
            f.write(base64.b64decode(b64.group(3)))
            f.close()

