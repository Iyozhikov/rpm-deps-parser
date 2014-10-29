import os
import re
import rpm


from var_dump import var_dump
from pprint import pprint


# VARS
specfile = "murano.spec"

RUNTIME_SECTIONS = ['%prep', '%build', '%install', '%clean', '%check']
METAINFO_SECTIONS = ['%header', '%package']
SPECFILE_SECTIONS = ['%header',
                     '%description',
                     '%package',
                     '%prep',
                     '%build',
                     '%install',
                     '%clean',
                     '%check',
                     '%files',
                     '%changelog']


def _get_pkg_by_name(pkg_name):
    '''
    Return package with given name. pgk_name == None
    -> base package, not existing name -> KeyError
    '''
    if not pkg_name:
        return spec.packages[0]
    for p in spec.packages:
        if p.header[rpm.RPMTAG_NAME] == pkg_name:
            return p
    raise KeyError(pkg_name + ': no such package')


def expand_tag(tag, pkg_name=None):
    '''
    Return value of given tag in the spec file, or None. Parameters:
      - tag: tag as listed by rpm --querytags, case-insensitive or
        a  constant like rpm.RPMTAG_NAME.
      - package: A subpackage, as listed by get_packages(), defaults
        to the source package.
    '''
    if not pkg_name:
        header = spec.sourceHeader
    else:
        header = (pkg_name).header
    try:
        return header[tag]
    except ValueError:
        return None
    except rpm._rpm.error:
        return None


def parse_spec():
    ''' Let rpm parse the spec and build spec.spec (sic!). '''
    try:
        spec = rpm.TransactionSet().parseSpec(specfile)
        return spec
    except Exception as ex:
        print "Can't parse specfile: " + ex.__str__()


spec = parse_spec()
_packages = None
name_vers_rel = [expand_tag(rpm.RPMTAG_NAME),
                 expand_tag(rpm.RPMTAG_VERSION),
                 '*']
name_vers_rel[2] = expand_tag(rpm.RPMTAG_RELEASE)

name = property(lambda: name_vers_rel[0])
version = property(lambda: name_vers_rel[1])
release = property(lambda: name_vers_rel[2])

pkgs = [p.header[rpm.RPMTAG_NAME] for p in spec.packages]

print pkgs
