""" This document contains utility functions to help create a valid submission
for CodaLab.

AS A PARTICIPANT, DO NOT MODIFY THIS CODE.
"""
import os 
from contextlib import closing
from zipfile import ZipFile, ZIP_DEFLATED

from absl import app
from absl import flags 
from absl import logging

FLAGS = flags.FLAGS

flags.DEFINE_string("directory", "../baselines/random/", "Directory to zip.")
flags.DEFINE_string("zip_name", "mysubmission.zip", "Zipped file name.")


def zipdir(archivename: str, basedir: str) -> None:
    """ Zip directory, from J.F. Sebastian http://stackoverflow.com/

    Args:
        archivename (str): Name for the zip file.
        basedir (str): Directory where the submission code is located.
    """
    assert os.path.isdir(basedir)
    with closing(ZipFile(archivename, "w", ZIP_DEFLATED)) as z:
        for root, _, files in os.walk(basedir):
            for fn in files:
                if not fn.endswith(".zip"):
                    absfn = os.path.join(root, fn)
                    zfn = absfn[len(basedir):] 
                    assert absfn[:len(basedir)] == basedir
                    if zfn[0] == os.sep:
                        zfn = zfn[1:]
                    z.write(absfn, zfn)


def main(argv):
    """ Zip a model directory to a valid code submission."""
    del argv
    model_dir = FLAGS.directory
    zip_name = FLAGS.zip_name
    logging.info("Starting zipping with model directory : {} in {}"
        .format(model_dir, zip_name))
    zipdir(zip_name, model_dir)
    logging.info("Submission ready in : {}".format(os.path.abspath(zip_name)))

if __name__ == "__main__":
    app.run(main)
