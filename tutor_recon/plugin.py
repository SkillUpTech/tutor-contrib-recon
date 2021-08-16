import os
import pkg_resources
from glob import glob

from tutor_recon.__about__ import __version__
from tutor_recon.commands.recon import recon

templates = pkg_resources.resource_filename("tutor_recon", "templates")

config = {}

hooks = {}


def patches():
    all_patches = {}
    patches_dir = pkg_resources.resource_filename("tutor_recon", "patches")
    for path in glob(os.path.join(patches_dir, "*")):
        with open(path) as patch_file:
            name = os.path.basename(path)
            content = patch_file.read()
            all_patches[name] = content
    return all_patches


command = recon
