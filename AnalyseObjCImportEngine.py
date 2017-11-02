#!/usr/bin/python
#  -*- coding:utf-8 -*-

import sys
import os
from sets import Set
import re
from os.path import basename
import argparse

local_regex_import = re.compile("^\s*#(?:import|include)\s+\"(?P<filename>\S*)(?P<extension>\.(?:h|hpp|hh))?\"")
system_regex_import = re.compile("^\s*#(?:import|include)\s+[\"<](?P<filename>\S*)(?P<extension>\.(?:h|hpp|hh))?[\">]")
objc_extensions = ['.h', '.hh', '.hpp', '.m', '.mm', '.c', '.cc', '.cpp']

class EngineObjCInputArgument:
      path       = None
      exclude    = None
      ignore     = None
      system     = False
      extensions = False
      root       = None
      specifyPath = None



class AnalyseItem:
    name      = None
    extension = None
    files     = None




class AnalyseObjCImportEngine:
    def __init__(self,argument):
        self.argument = argument
        self.noReSet = Set()


    def startAnalyseSpecifyPath(self):

        specifySet = Set()

        if self.argument.specifyPath != None:
            for root, dirs, files in os.walk(self.argument.specifyPath):
                objc_files = (f for f in files if f.endswith('.h'))
                m = Set()
                isHasItem = False
                for f in objc_files:
                    isHasItem = True
                    filename = os.path.splitext(f)[0]
                    m.add(filename)
                if(isHasItem):
                    specifySet.add(m)

        print(specifySet)

        h_set = self.dependencies_include_category_in_project(self.argument.path, '.h', self.argument.exclude, self.argument.ignore,
                                               self.argument.system, self.argument.extensions,specifySet)
        m_set = self.dependencies_include_category_in_project(self.argument.path, '.m', self.argument.exclude, self.argument.ignore,
                                             self.argument.system, self.argument.extensions,specifySet)

        print('111111111没有使用的类')
        for m in specifySet:
            for n in m:
                if n not in self.noReSet:
                    print (n)
        print ('222222222')


        d = {}

        for (k, v) in h_set.iteritems():
            if not k in d:
                d[k] = Set()
            d[k] = d[k].union(v)

        for (k, v) in m_set.iteritems():
            if not k in d:
                d[k] = Set()
            d[k] = d[k].union(v)
        print ('-----------------')
        print (d)
        f = open('1.dot','w')
        f.write('digraph G {')
        f.write('subgraph clusterA  {')
        f.write('style=filled;')
        f.write('bgcolor=red;')
        mIndex = 0
        for m in specifySet:
            f.write('\n\tsubgraph cluster%s  {' %mIndex)
            f.write('\n\tstyle=filled;')
            f.write('\tcolor=blue;')
            for n in m:
                f.write('\n\t%s;' % (n))
            f.write('\n}')
            mIndex = mIndex + 1
        f.write('}')


        f.write('\n\tnode [shape=box];')
        for (k, v) in d.iteritems():
            f.write('\n\tnode [shape=box];')
            for x in v:
                f.write("\n\t\"%s\" -> \"%s\" [color=red];" % (k, x))

        f.close()







    def startAnalyse(self):
        print('begin')
        d = self.dependencies_in_project_with_file_extensions(self.argument.path,objc_extensions,self.argument.exclude,self.argument.ignore,self.argument.system,self.argument.extensions,self.argument.root)
        two_ways_set        = self.two_ways_dependencies(d)
        untraversed_set     = self.untraversed_files(d)
        category_list, d    = self.category_files(d)
        pch_set             = self.dependencies_in_project(self.argument.path, '.pch', self.argument.exclude, self.argument.ignore, self.argument.system, self.argument.extensions)
        sys.stderr.write("# number of imports\n\n")
        self.print_frequencies_chart(d)

        sys.stderr.write("\n# times the class is imported\n\n")
        d2 = self.referenced_classes_from_dict(d)
        self.print_frequencies_chart(d2)

        #

        l = []
        l.append("digraph G {")
        l.append("\tnode [shape=box];")

        for k, deps in d.iteritems():
            if deps:
                deps.discard(k)

            if len(deps) == 0:
                l.append("\t\"%s\" -> {};" % (k))

            for k2 in deps:
                if not ((k, k2) in two_ways_set or (k2, k) in two_ways_set):
                    l.append("\t\"%s\" -> \"%s\";" % (k, k2))

        l.append("\t")
        for (k, v) in pch_set.iteritems():
            l.append("\t\"%s\" [color=red];" % k)
            for x in v:
                l.append("\t\"%s\" -> \"%s\" [color=red];" % (k, x))

        l.append("\t")
        l.append("\tedge [color=blue, dir=both];")

        for (k, k2) in two_ways_set:
            l.append("\t\"%s\" -> \"%s\";" % (k, k2))

        for k in untraversed_set:
            l.append("\t\"%s\" [color=gray, style=dashed, fontcolor=gray]" % k)

        if category_list:
            l.append("\t")
            l.append("\tedge [color=black];")
            l.append("\tnode [shape=plaintext];")
            l.append("\t\"Categories\" [label=\"%s\"];" % "\\n".join(category_list))

        if self.argument.ignore:
            l.append("\t")
            l.append("\tnode [shape=box, color=blue];")
            l.append("\t\"Ignored\" [label=\"%s\"];" % "\\n".join(ignore))

        l.append("}\n")
        print ('\n'.join(l))

    def referenced_classes_from_dict(self,d):
        d2 = {}

        for k, deps in d.iteritems():
            for x in deps:
                d2.setdefault(x, Set())
                d2[x].add(k)

        return d2

    def print_frequencies_chart(self,d):

        lengths = map(lambda x: len(x), d.itervalues())
        if not lengths: return
        max_length = max(lengths)

        for i in range(0, max_length + 1):
            s = "%2d | %s\n" % (i, '*' * lengths.count(i))
            sys.stderr.write(s)

        sys.stderr.write("\n")

        l = [Set() for i in range(max_length + 1)]
        for k, v in d.iteritems():
            l[len(v)].add(k)

        for i in range(0, max_length + 1):
            s = "%2d | %s\n" % (i, ", ".join(sorted(list(l[i]))))
            sys.stderr.write(s)

    def category_files(self,d):
        d2 = {}
        l = []

        for k, v in d.iteritems():
            if not v and '+' in k:
                l.append(k)
            else:
                d2[k] = v

        return l, d2

    def untraversed_files(self,d):

        dead_ends = Set()

        for file_a, file_a_dependencies in d.iteritems():
            for file_b in file_a_dependencies:
                if not file_b in dead_ends and not file_b in d:
                    dead_ends.add(file_b)

        return dead_ends

    def dependencies_in_project_with_file_extensions(self,path, exts, exclude, ignore, system, extensions, root_class):

        d = {}

        for ext in exts:
            d2 = self.dependencies_in_project(path, ext, exclude, ignore, system, extensions)
            for (k, v) in d2.iteritems():
                if not k in d:
                    d[k] = Set()
                d[k] = d[k].union(v)

        if root_class:
            def parse_requirements(tree, root, known_deps=[]):
                next_deps = list(tree[root])
                new_deps = []

                for dep in next_deps:
                    if dep not in known_deps and dep in tree:
                        new_deps += parse_requirements(tree, dep, known_deps + next_deps)

                return (new_deps + next_deps)

            requirements = set(parse_requirements(d, root_class))

            return {k: d[k] for k in requirements if k in d}

        return d

    def dependencies_include_category_in_project(self, path, ext, exclude, ignore, system, extensions,specifySet):
        d = {}

        regex_exclude = None
        if exclude:
            regex_exclude = re.compile(exclude)

        for root, dirs, files in os.walk(path):

            if ignore:
                for subfolder in ignore:
                    if subfolder in dirs:
                        dirs.remove(subfolder)

            objc_files = (f for f in files if f.endswith(ext))

            for f in objc_files:

                filename = f if extensions else os.path.splitext(f)[0]
                if regex_exclude is not None and regex_exclude.search(filename):
                    continue

                if filename not in d:
                    d[filename] = Set()

                path = os.path.join(root, f)

                for imported_filename in self.gen_filenames_imported_in_file(path, regex_exclude, system, extensions):
                    if '/' in imported_filename:
                        imported_filename = imported_filename.split('/', 1)[-1]
                    print ('imported_filename:'+imported_filename)
                    print ('filename:'+filename)
                    if filename != (os.path.splitext(imported_filename)[0]) :
                        imported_filename = imported_filename if extensions else os.path.splitext(imported_filename)[0]
                        for mSet in specifySet:
                            if imported_filename in mSet :
                                self.noReSet.add(imported_filename)
                                d[filename].add(imported_filename)
                                break



        return d

    def dependencies_in_project(self,path, ext, exclude, ignore, system, extensions):
        d = {}

        regex_exclude = None
        if exclude:
            regex_exclude = re.compile(exclude)

        for root, dirs, files in os.walk(path):

            if ignore:
                for subfolder in ignore:
                    if subfolder in dirs:
                        dirs.remove(subfolder)

            objc_files = (f for f in files if f.endswith(ext))

            for f in objc_files:

                filename = f if extensions else os.path.splitext(f)[0]
                if regex_exclude is not None and regex_exclude.search(filename):
                    continue

                if filename not in d:
                    d[filename] = Set()

                path = os.path.join(root, f)

                for imported_filename in self.gen_filenames_imported_in_file(path, regex_exclude, system, extensions):
                    if imported_filename != filename and '+' not in imported_filename and '+' not in filename:
                        imported_filename = imported_filename if extensions else os.path.splitext(imported_filename)[0]
                        d[filename].add(imported_filename)

        return d

    def gen_filenames_imported_in_file(self,path, regex_exclude, system, extensions):
        for line in open(path):
            results = re.search(system_regex_import, line) if system else re.search(local_regex_import, line)
            if results:
                filename = results.group('filename')
                extension = results.group('extension') if results.group('extension') else ""
                print ('gen:'+filename+extension)
                if regex_exclude is not None and regex_exclude.search(filename + extension):
                    continue
                yield (filename + extension) if extension else filename

    def two_ways_dependencies(self,d):

        two_ways = Set()

        for a, l in d.iteritems():
            for b in l:
                if b in d and a in d[b]:
                    if (a, b) in two_ways or (b, a) in two_ways:
                        continue
                    if a != b:
                        two_ways.add((a, b))

        return two_ways


if __name__=='__main__':
    argument = EngineObjCInputArgument()
    argument.path       = "/Users/heboyce/Desktop/ELEProject/Crowdsource-iOS"
    argument.exclude    = None
    argument.ignore     = "/Users/heboyce/Desktop/ELEProject/Crowdsource-iOS/Pods/LPDQualityControlKit"
    argument.system     = True
    argument.extensions = False
    argument.root       = None
    argument.specifyPath = "/Users/heboyce/Desktop/ELEProject/Crowdsource-iOS/Pods/LPDQualityControlKit"

    engine = AnalyseObjCImportEngine(argument)
    engine.startAnalyseSpecifyPath()