mangasteal
==========

Manga Scraper and PDF generator

Scrapes images from mangafox and turns downloaded images into single PDF file.

Usage
=========

Dependencies

1. node + (async, jquery, underscore)
2. imagemagick
3. pypdf

Steps to use:

1) Scrape for images
    node download_mangafox.js [mangafox manga URL]
    cd [manga name]/
3) Convert jpgs into pdfs
    ls **/*.jpg | xargs morgify --format pdf
    cd ..
5) Create PDF file (temporary chapters and volumes in /tmp/[manga name])
    python topdf.py [manga name]/

