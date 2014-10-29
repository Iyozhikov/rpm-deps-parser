from var_dump import var_dump
from spec_file import SpecFile
import rpm
import re
import os

# VARS
filename = "murano.spec"
# filename = "/home/iyozhikov/WorkSpace/git/OSCI/heat-build/rpm" \
#            "/SPECS/openstack-heat.spec"
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

specs = []


def ReadFromFS(file):
    try:
        with open(file) as f:
            specs.append(f.readlines())
    except IOError as e:
        print('Could not open file: {0}'.format(e))
        sys.exit(1)


class Convertor(object):

    def __init__(self, spec, options=None):
        spec = self.list_to_str(spec)
        self.original_spec = spec
        self.options = options or {}

    def list_to_str(self, arg):
        if not isinstance(arg, str):
            arg = ''.join(arg)
        return arg


class SpecFile(object):

    def __init__(self, specfile):
        if not isinstance(specfile, str):
            self.specfile = ''.join(specfile)
        else:
            self.specfile = specfile

        self.sections = self.split_sections()

    def get_sections_new(self):
        for ssection in SPECFILE_SECTIONS:
            match = re.match('^' + ssection, self.specfile, re.M)
            print match
            if match:
                print match.group(0)

    def split_sections(self):
        headers_re = [re.compile('^' + x, re.M) for x in SPECFILE_SECTIONS]
        section_starts = []
        for header in headers_re:
            for match in header.finditer(self.specfile):
                section_starts.append(match.start())

        section_starts.sort()
        header_end = section_starts[0] if section_starts else len(self.specfile)
        sections = [('%header', self.specfile[:header_end])]
        for i in range(len(section_starts)):
            if len(section_starts) > i + 1:
                curr_section = self.specfile[section_starts[i]:
                                             section_starts[i + 1]
                                             ]
            else:
                curr_section = self.specfile[section_starts[i]:]
            for header in headers_re:
                if header.match(curr_section):
                    sections.append((header.pattern[1:], curr_section))

        return sections

    def __contains__(self, what):
        return reduce(lambda x, y: x or (what in y[1]), self.sections, False)

    def __str__(self):
        return '\n\n'.join([section for section in list(zip(*self.sections))[1] if section])


def get_original_name(section):
        name_match = re.compile(r'Name:\s*([^\s]+)').search(section)
        if name_match:
            return name_match.group(1)
        else:
            return 'TODO'


def get_head(sections):
    for i, section in enumerate(sections):
        if section[0] == '%header':
            return section[1]


def get_all_tags(sections):
    tags = []
    for i, section in enumerate(sections):
        tags.append(section[0])
    return tags


def parse_requires(raw_require_string):
    elements = raw_require_string.split(', ')
    pkg_info = {'name': '', 'conditions': [], 'versions': []}
    for i in range(len(elements)):
        element = elements[i]
        element_parts = elements[i].split(' ')
        element_name = element_parts[0]
        if len(element_parts) == 1 and i == 0:
            pkg_info['name'] = element_name
        elif len(element_parts) > 1 and i == 0:
            pkg_info['name'] = element_name
            pkg_info['conditions'].append(element_parts[1])
            pkg_info['versions'].append(element_parts[2])
        else:
            cond_len = len(pkg_info['conditions'])
            ver_len = len(pkg_info['versions'])
            if (
                element_parts[1] != pkg_info['conditions'][cond_len-1] and
                element_parts[2] != pkg_info['versions'][ver_len-1]
            ):
                pkg_info['conditions'].append(element_parts[1])
                pkg_info['versions'].append(element_parts[2])
            elif (
                element_parts[1] != pkg_info['conditions'][cond_len-1] and
                element_parts[2] == pkg_info['versions'][ver_len-1]
            ):
                pkg_info['conditions'][cond_len-1] = "!="
    return pkg_info


def pp_req_vers(info_obj):
    result = ''
    name = info_obj['name']
    for i in range(len(info_obj['conditions'])):
        if not result:
            result += "%s%s" % (info_obj['conditions'][i],
                                info_obj['versions'][i])
        else:
            result += ",%s%s" % (info_obj['conditions'][i],
                                 info_obj['versions'][i])
    return "%s%s" % (name, result)


def get_section(sections, section_name=None):
    keys = []
    value = []
    for i, section in enumerate(sections):
        if section_name:
            if section[0] == section_name:
                package_name = None
                #match = re.search('(?<=^%package) [\w+-].*', section[1])
                #
                matches_re_main = re.compile('^\s*Requires:\s*([^\s\%]+.*$)',
                                             re.M)
                for match in matches_re_main.finditer(section[1]):
                    req_item = ''.join(match.groups())
                    retval = parse_requires(req_item)
                    print " - %s %s" % (main_package_name,
                                     pp_req_vers(retval))
                #
                match = re.compile(r''+section_name+'\s*([^\s]+)'). \
                    search(section[1])
                if match:
                    package_name = match.group(1)
                if package_name:
                    print "  Child: %s" % (main_package_name+'-'+package_name)
                    # req_pkg_info = {'name': '', 'conditions': [],
                    #                 'versions': []}
                    # #matches_re = re.compile('^\s*Requires:\s*([^\s]+.*$)', re.M)
                    matches_re = re.compile('^\s*Requires:\s*([^\s\%]+.*$)',
                                            re.M)
                    for match in matches_re.finditer(section[1]):
                        reququired_item = ''.join(match.groups())

                        retval = parse_requires(reququired_item)
                        print "   - %s %s" % (main_package_name+'-'+package_name,
                                              pp_req_vers(retval))
        else:
            print "i=%s;sections=%s" % (i, section[0])


ReadFromFS(filename)
for spec in specs:
    specfile = SpecFile(spec)
    #print get_all_tags(specfile.sections)
    main_package_name = get_original_name(get_head(specfile.sections))
    print "Parent: %s" % main_package_name
    #get_section(specfile.sections)
    matches_re_main = re.compile('^\s*Requires:\s*([^\s\%]+.*$)',
                                 re.M)
    for match in matches_re_main.finditer(get_head(specfile.sections)):
        req_item = ''.join(match.groups())
        retval = parse_requires(req_item)
        print " - %s %s" % (main_package_name,
                            pp_req_vers(retval))
    #
    #get_section(specfile.sections, '%package')
    #print get_section(specfile.sections)

# spec = SpecFile(filename)
# spec.get_sections()
