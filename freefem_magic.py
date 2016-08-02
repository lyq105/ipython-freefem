"""
An IPython extension for generating and displaying ffmptote figures within
an IPython notebook. Refer to examples directory for usage examples.
"""
import os
import shutil
import subprocess
import tempfile
from IPython.core.magic import (
    magics_class, line_magic, line_cell_magic, Magics)
from IPython.core.magic_arguments import (
    argument, magic_arguments, parse_argstring)
from IPython.display import Image, SVG

try:
    from wand.image import Image as WImage
except ImportError:

    #print "Python Library wand is not installed! Some functional may not usable."
    is_have_wand = False

class FreeFemException(RuntimeError):
    """
    Simple wrapper class for wrapping Freefem
    interpreter error messages in a stack trace.
    """

    def __init__(self, freefem_err_msg):
        self.freefem_err_msg = freefem_err_msg

    def __str__(self):
        return str(self.freefem_err_msg)

class TemporaryFreeFemFile(object):
    """
    Temporary locations to write freefem code files
    compatible with python's "with" construct.
    """

    def __init__(self, ff_codes):
        """
        Parameters
        ----------
        ff_code : list(str) - list of strings, each string
            corresponding to code for an Asymptote file
            (including newlines, etc).
        """
        self.tmp_dir = tempfile.mkdtemp()
        self.ff_files = []
        if not isinstance(ff_codes, list):
            ff_codes = [ff_codes]
        for ff_code in ff_codes:
            ff_fd, ff_file = tempfile.mkstemp(
                suffix=".edp", dir=self.tmp_dir)
            with os.fdopen(ff_fd, "w") as ff_fh:
                ff_fh.write(ff_code)
            self.ff_files.append(ff_file)

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        shutil.rmtree(self.tmp_dir)

@magics_class
class FreeFemMagic(Magics):
    """
    Define a line/cell IPython magic %freefem++ which takes
    a pre-existing ff code file and additional Freefem++ code
    entered into the IPython cell, and outputs image
    rendered by Asymptote.

    """
    def __init__(self, shell, cache_display_data=False):
        super(FreeFemMagic, self).__init__(shell)
        self.cache_display_data = cache_display_data

    @magic_arguments()
    @argument(
        'ff_file', nargs="?",
        help="Name of existing .edp file"
        )
    @argument(
        '-dp', '--display',
        help="Display Freefem output picture, especially the .eps"
        )
    @argument(
        '-dsvg', '--displaysvg',
        help="Display Freefem output picture in .svg format"
        )
    @argument(
        '-w', '--write',
        help="Save Freefem code to this root path"
        )
    @line_cell_magic
    def freefem(self, line, cell=None):
        """Run Freefem++ code.

        To run an existing .edp file, use the IPython magic:

            %freefem filename.edp

        Asymptote code can also be entered into an IPython cell:

            %%freefem


        This writes the cell's contents to a temporary .edp file and
        outputs a temporary image for IPython to display. By default,
        the image is a png, since this requires the least setup. This
        can be changed using the -f argument, although FreeFem++ may
        require other third-party programs like ImageMagick for other
        formats. The ff file and image can be saved to a non-temporary
        location using the -r argument (Freefem code will be saved to
        root.ff and image to root.image_extension).
        """
        args = parse_argstring(self.freefem, line)
	ff_file = 'temp.edp'

        if cell is not None:

            if args.write:
                # If write option is specified, retain intermediate .edp file.
                ff_file = args.write + ".edp"
            with open(ff_file, "w") as ff_fh:
                    ff_fh.write(cell)

        if args.ff_file:
            ff_file = args.ff_file


        std_out = self.run_ff_file(ff_file)

        if args.display:
    	    return Image(filename=self.convert_png(args.display))

        if args.displaysvg:
            return SVG(filename=self.convert_svg(args.displaysvg))



    def convert_png(self,img_eps_file):

        if not os.path.exists(img_eps_file):
            raise IOError("File not found: " + ff_file)

        converter_proc = subprocess.Popen(["inkscape",'-z','-f', img_eps_file, '-e', img_eps_file+'.png'],
        #converter_proc = subprocess.Popen(["convert", img_eps_file, img_eps_file+'.png'],
                                stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (ff_stdout,ff_stderr) = converter_proc.communicate()

        if converter_proc.returncode != 0:
	    raise FreeFemException(ff_stdout)

        print(ff_stdout)
        return img_eps_file+'.png'

    def convert_svg(self,img_eps_file):

        if not os.path.exists(img_eps_file):
            raise IOError("File not found: " + ff_file)

        converter_proc = subprocess.Popen(["inkscape",'-z','-f', img_eps_file, '-l', img_eps_file+'.svg'],
        #converter_proc = subprocess.Popen(["convert", img_eps_file, img_eps_file+'.svg'],
                                stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (ff_stdout,ff_stderr) = converter_proc.communicate()

        if converter_proc.returncode != 0:
	    raise FreeFemException(ff_stdout)

        print(ff_stdout)
        return img_eps_file+'.svg'

    def run_ff_file(self, ff_file):
        """Runs ffmptote code located in ff_file and writes to
        img_file if specified, otherwise use's ffmptote's default
        output location. Returns tuple (IPython.display, stdout).
        """
        if not os.path.exists(ff_file):
            raise IOError("File not found: " + ff_file)

        ff_proc = subprocess.Popen(["FreeFem++",'-nowait','-nw','-ne', ff_file],
                                stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (ff_stdout,ff_stderr) = ff_proc.communicate()
        if ff_proc.returncode != 0:
	    raise FreeFemException(ff_stdout)
        print(ff_stdout)

        return ff_stdout

def load_ipython_extension(ipython):
    ipython.register_magics(FreeFemMagic)
