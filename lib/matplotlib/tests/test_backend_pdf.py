# -*- encoding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import six

import io
import os
import tempfile

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch
from nose.tools import raises

import numpy as np
from matplotlib import checkdep_tex, cm, rcParams
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import pyplot as plt
from matplotlib.testing.determinism import (_determinism_source_date_epoch,
                                            _determinism_check)
from matplotlib.testing.decorators import (image_comparison, knownfailureif,
                                           cleanup)
from matplotlib import dviread


@image_comparison(baseline_images=['pdf_use14corefonts'],
                  extensions=['pdf'])
def test_use14corefonts():
    rcParams['pdf.use14corefonts'] = True
    rcParams['font.family'] = 'sans-serif'
    rcParams['font.size'] = 8
    rcParams['font.sans-serif'] = ['Helvetica']
    rcParams['pdf.compression'] = 0

    text = '''A three-line text positioned just above a blue line
and containing some French characters and the euro symbol:
"Merci pépé pour les 10 €"'''

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.set_title('Test PDF backend with option use14corefonts=True')
    ax.text(0.5, 0.5, text, horizontalalignment='center',
            verticalalignment='bottom',
            fontsize=14)
    ax.axhline(0.5, linewidth=0.5)

needs_tex = knownfailureif(
    not checkdep_tex(),
    "This test needs a TeX installation")


@cleanup
def test_type42():
    rcParams['pdf.fonttype'] = 42

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot([1, 2, 3])
    fig.savefig(io.BytesIO())


@cleanup
def test_multipage_pagecount():
    with PdfPages(io.BytesIO()) as pdf:
        assert pdf.get_pagecount() == 0
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot([1, 2, 3])
        fig.savefig(pdf, format="pdf")
        assert pdf.get_pagecount() == 1
        pdf.savefig()
        assert pdf.get_pagecount() == 2


@cleanup
def test_multipage_keep_empty():
    from matplotlib.backends.backend_pdf import PdfPages
    from tempfile import NamedTemporaryFile
    # test empty pdf files
    # test that an empty pdf is left behind with keep_empty=True (default)
    with NamedTemporaryFile(delete=False) as tmp:
        with PdfPages(tmp) as pdf:
            filename = pdf._file.fh.name
        assert os.path.exists(filename)
    os.remove(filename)
    # test if an empty pdf is deleting itself afterwards with keep_empty=False
    with PdfPages(filename, keep_empty=False) as pdf:
        pass
    assert not os.path.exists(filename)
    # test pdf files with content, they should never be deleted
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot([1, 2, 3])
    # test that a non-empty pdf is left behind with keep_empty=True (default)
    with NamedTemporaryFile(delete=False) as tmp:
        with PdfPages(tmp) as pdf:
            filename = pdf._file.fh.name
            pdf.savefig()
        assert os.path.exists(filename)
    os.remove(filename)
    # test that a non-empty pdf is left behind with keep_empty=False
    with NamedTemporaryFile(delete=False) as tmp:
        with PdfPages(tmp, keep_empty=False) as pdf:
            filename = pdf._file.fh.name
            pdf.savefig()
        assert os.path.exists(filename)
    os.remove(filename)


@cleanup
def test_composite_image():
    # Test that figures can be saved with and without combining multiple images
    # (on a single set of axes) into a single composite image.
    X, Y = np.meshgrid(np.arange(-5, 5, 1), np.arange(-5, 5, 1))
    Z = np.sin(Y ** 2)
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.set_xlim(0, 3)
    ax.imshow(Z, extent=[0, 1, 0, 1])
    ax.imshow(Z[::-1], extent=[2, 3, 0, 1])
    plt.rcParams['image.composite_image'] = True
    with PdfPages(io.BytesIO()) as pdf:
        fig.savefig(pdf, format="pdf")
        assert len(pdf._file._images.keys()) == 1
    plt.rcParams['image.composite_image'] = False
    with PdfPages(io.BytesIO()) as pdf:
        fig.savefig(pdf, format="pdf")
        assert len(pdf._file._images.keys()) == 2


@cleanup
def test_source_date_epoch():
    """Test SOURCE_DATE_EPOCH support for PDF output"""
    _determinism_source_date_epoch("pdf", b"/CreationDate (D:20000101000000Z)")


@cleanup
def test_determinism_plain():
    """Test for reproducible PDF output: simple figure"""
    _determinism_check('', format="pdf")


@cleanup
def test_determinism_images():
    """Test for reproducible PDF output: figure with different images"""
    _determinism_check('i', format="pdf")


@cleanup
def test_determinism_hatches():
    """Test for reproducible PDF output: figure with different hatches"""
    _determinism_check('h', format="pdf")


@cleanup
def test_determinism_markers():
    """Test for reproducible PDF output: figure with different markers"""
    _determinism_check('m', format="pdf")


@cleanup
def test_determinism_all():
    """Test for reproducible PDF output"""
    _determinism_check(format="pdf")


@image_comparison(baseline_images=['hatching_legend'],
                  extensions=['pdf'])
def test_hatching_legend():
    """Test for correct hatching on patches in legend"""
    fig = plt.figure(figsize=(1, 2))

    a = plt.Rectangle([0, 0], 0, 0, facecolor="green", hatch="XXXX")
    b = plt.Rectangle([0, 0], 0, 0, facecolor="blue", hatch="XXXX")

    fig.legend([a, b, a, b], ["", "", "", ""])


@image_comparison(baseline_images=['grayscale_alpha'],
                  extensions=['pdf'])
def test_grayscale_alpha():
    """Masking images with NaN did not work for grayscale images"""
    x, y = np.ogrid[-2:2:.1, -2:2:.1]
    dd = np.exp(-(x**2 + y**2))
    dd[dd < .1] = np.nan
    fig, ax = plt.subplots()
    ax.imshow(dd, interpolation='none', cmap='gray_r')
    ax.set_xticks([])
    ax.set_yticks([])


@cleanup
@needs_tex
@raises(ValueError)
@patch('matplotlib.dviread.PsfontsMap.__getitem__')
def test_missing_psfont(mock):
    """An error is raised if a TeX font lacks a Type-1 equivalent"""
    psfont = dviread.PsFont(texname='texfont', psname='Some Font',
                            effects=None, encoding=None, filename=None)
    mock.configure_mock(return_value=psfont)
    rcParams['text.usetex'] = True
    fig, ax = plt.subplots()
    ax.text(0.5, 0.5, 'hello')
    with tempfile.TemporaryFile() as tmpfile:
        fig.savefig(tmpfile, format='pdf')
