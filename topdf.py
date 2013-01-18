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
    latex = """
    \\documentclass{article}
    \\usepackage{pdfpages}
    \\begin{document}
    %s
    \\end{document}
    """
    includes = []
    for pdf in pdfs:
        if check_rotate:
            try:
                img = Image.open(pdf[:-4] + '.jpg')
            except Exception as e:
                print e
                continue
            w,h = img.size
            if w > h:
                includes.append('\immediate\includepdf[landscape, angle=-90]{%s}' % pdf)
            else:
                includes.append('\immediate\includepdf[landscape]{%s}' % pdf)
        else:
            includes.append('\immediate\includepdf[landscape]{%s}' % pdf)

    latex = latex % '\n'.join(includes)
    with file('./latex.tex', 'w') as f:
        f.write(latex)
    os.system('pdflatex latex.tex > latex.err 2> latex.err; mv latex.pdf %s' % fname)

def create_chapters(manga_root_dir, outdir, create=True):
    """
    chapters are written into temporary files in /tmp/{manga_root_dir}
    """

    volumes = defaultdict(list)
    for dirpath, dirnames, fnames in os.walk('./'):
        jpgs = filter(fendswith('jpg'), fnames)
        pdfs = filter(fendswith('pdf'), fnames)
        if not pdfs or not jpgs: continue


        folders = dirpath[2:].split('/')
        vol = folders[0]
        fpath = '_'.join(folders)
        fpath = os.path.join(outdir, '%s.pdf' % fpath)
        print fpath

        pdfs = [os.path.join(dirpath, pdf) for pdf in pdfs]
        if create:
            chapter_pdf(fpath, pdfs, True)
        volumes[vol].append(fpath)
    return volumes


def create_manga(manga_root_dir, build_chapters=True):
    """
    @param volumes mapping from volume name to list of chapter pdfs
    """
    manganame = re.sub('[^\w\s]', '', manga_root_dir.lower()).replace(' ', '_')
    outdir = os.path.join('/tmp/', manga_root_dir)
    os.system('mkdir -p %s' % outdir)


    volumes = create_chapters(manga_root_dir, outdir,  create=build_chapters)

    # merge chapters into volumes
    volpdfs = []
    for vol, pdfs in volumes.items():
        print vol
        pdfs.sort()
        fname = os.path.join(outdir,'%s.pdf' % vol)
        volpdfs.append(fname)
        merge_pdf(fname, pdfs)


    # merge volumes into manga
    merge_pdf('./%s.pdf' % manganame, sorted(volpdfs))



if __name__ == '__main__':
    print sys.argv
    manga_root_dir = sys.argv[1]
    create_manga(manga_root_dir)
