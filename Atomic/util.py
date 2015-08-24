import collections
import docker
import selinux
import subprocess
import sys
from fnmatch import fnmatch as matches

"""Atomic Utility Module"""

ReturnTuple = collections.namedtuple('ReturnTuple',
                                     ['return_code', 'stdout', 'stderr'])

if sys.version_info[0] < 3:
    input = raw_input
else:
    input = input


def image_by_name(img_name):
    """
    Returns a list of image data for images which match img_name.
    """
    def _repo_tag_matches(tag, name):
        """
        Returns whether a tag matches an image, e.g.
        "registry/user/image:tag" will be matched by "image", "user/image",
        "registry/user/image", with or without appended ":tag".
        """
        return any([matches(tag, '*/'+name+':*'),
                    matches(tag, '*/'+name),
                    matches(tag, name+':*'),
                    matches(tag, name)])

    def _repo_tags_match(tags, name):
        return any([_repo_tag_matches(tag, name) for tag in tags])

    c = docker.Client()

    images = c.images(all=False)
    valid_images = []

    return [i for i in images if _repo_tags_match(i['RepoTags'], img_name)]


def subp(cmd):
    """
    Run a command as a subprocess.
    Return a triple of return code, standard out, standard err.
    """
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return ReturnTuple(proc.returncode, stdout=out, stderr=err)


def default_container_context():
    if selinux.is_selinux_enabled() != 0:
        fd = open(selinux.selinux_lxc_contexts_path())
        for i in fd.readlines():
            name, context = i.split("=")
            if name.strip() == "file":
                return context.strip("\n\" ")
    return ""


def writeOut(output, lf="\n"):
    sys.stdout.flush()
    sys.stdout.write(str(output) + lf)