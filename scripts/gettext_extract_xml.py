import os
import sys
from toolib.util.paths import iterFilePaths
from toolib.util.reprs import repr
from wmlib.webkit.FormDom import Dom
from gettext_config import FORMS, FORMS_OUTPUT, FORMS_ATTRS
import time
import xml.dom
from toolib.util import strings



def main(output = FORMS_OUTPUT, *inputPaths):

	inputPaths = inputPaths or FORMS


	text = []
	code = []
	for path in inputPaths:
		for f in iterFilePaths(path):
			print 'Processing', f
			dom = Dom(f)
			for i in dom.iterNodesRecursive(xml.dom.Node.ELEMENT_NODE):
				for a in FORMS_ATTRS:
					attr = i.getAttribute(a)
					if attr:
						if not attr in text:
							text.append(attr)

			# extract code from forms
			for i in dom.iterNodesRecursiveFiltered(lambda node: node.nodeType in (xml.dom.Node.TEXT_NODE, xml.dom.Node.CDATA_SECTION_NODE)):
				if i.parentNode.tagName in ('trigger', 'action', 'total', 'calc'):
					data = i.data.rstrip()
					if data:
						code.extend(
							strings.stripText(data, lchars='\t ', preserveIndent=True, noJoin=True)
						)

	out = open(output, 'wt')
	print >> out, "# -*- coding: %s -*-\n" % sys.getdefaultencoding()
	print >> out, "# Automatically generated by %s\n"  % __file__

	for i in text:
		print >> out, "_(%s)" % repr(i)

	for i in code:
		print >> out, i

	out.close()

if __name__ == '__main__':
	from toolib import startup
	startup.startup()

	main(*sys.argv[1:])
