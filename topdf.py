from collections import defaultdict
import PIL.Image as Image
import os
import re
import sys



def tc(methodname, *args, **kwargs):
    return lambda o: o.__getattribute__(methodname)(*args, **kwargs)
tailcall = tc

def fendswith(suffix):
    return tailcall('endswith', suffix)

# merge the chapters per volume
from pyPdf import PdfFileWriter, PdfFileReader
def merge_pdf(fname, pdfs):

    output = PdfFileWriter()
    for pdf in pdfs:
        r = PdfFileReader(file(pdf, "rb"))
        for i in r.pages:
            output.addPage(i)
    with file(fname, 'wb') as outf:
        output.write(outf)


def chapter_pdf(fname, pdfs, check_rotate=False):
    """
    Pretty much the same as merge_pdf but rotates images to fill the page
    """
    output = PdfFileWriter()
    rfiles = [file(pdf, 'rb') for pdf in pdfs]
    for rf in rfiles:
        r = PdfFileReader(rf)
        for i in r.pages:
            w, h = i.artBox.getWidth(), i.artBox.getHeight()
            if w > h:
                i.rotateClockwise(90)
            output.addPage(i)

    with file(fname, 'wb') as outf:
        output.write(outf)
    for rf in rfiles:
        rf.close()


def create_chapters(manga_root_dir, outdir, create=True, debug=False):
    """
    chapters are written into temporary files in /tmp/{manga_root_dir}
    """
    outdir = os.path.join(outdir, 'chapters')
    os.system('mkdir -p %s' % outdir)

    volumes = defaultdict(list)
    for dirpath, dirnames, fnames in os.walk('./'):
        jpgs = filter(fendswith('jpg'), fnames)
        pdfs = filter(fendswith('pdf'), fnames)
        if not pdfs or not jpgs: continue


        folders = dirpath[2:].split('/')
        vol = folders[-2]
        fpath = '_'.join(folders)
        fpath = os.path.join(outdir, '%s.pdf' % fpath)
        print fpath

        pdfs = [os.path.join(dirpath, pdf) for pdf in pdfs]
        if create:
            chapter_pdf(fpath, pdfs, True)
        volumes[vol].append(fpath)

        if debug:
            break

    return volumes


def create_manga(manga_root_dir, outdir, build_chapters=True, debug=False):
    """
    @param volumes mapping from volume name to list of chapter pdfs
    """
    manganame = re.sub('[^\w\s]', '', manga_root_dir.lower()).replace(' ', '_')
    os.system('mkdir -p %s' % outdir)
    voloutdir = os.path.join(outdir, 'vols')
    os.system('mkdir -p %s' % voloutdir)


    volumes = create_chapters(manga_root_dir, outdir,  create=build_chapters, debug=debug)

    # merge chapters into volumes
    volpdfs = []
    for vol, pdfs in volumes.items():
        pdfs.sort()
        fname = os.path.join(voloutdir,'%s.pdf' % vol)
        volpdfs.append(fname)
        print fname
        merge_pdf(fname, pdfs)

    # merge volumes into manga
    merge_pdf('./%s.pdf' % manganame, sorted(volpdfs))



if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Create a manga PDF using directory of images scraped from MangaFox')
    parser.add_argument('-c', '--chapters', action='store_const', const=True, default=False, help='Should recreate new chapters?')
    parser.add_argument('-d', '--debug', action='store_const', const=True, default=False, help='render a single chapter')
    parser.add_argument('-o', '--output', default=None, help="Directory to output intermediate files")
    parser.add_argument('manga_root_dir')
    ns = parser.parse_args()


    build_chapters = ns.chapters
    manga_root_dir = ns.manga_root_dir
    debug = ns.debug
    outdir = ns.output or os.path.join('/tmp/', manga_root_dir)

    create_manga(manga_root_dir, outdir, build_chapters=True, debug=debug)
