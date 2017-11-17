#!/usr/bin/env python
import weakref
from typing import List, Dict, Any, Tuple, Union, Optional
from xml.etree.ElementTree import TreeBuilder, tostring
import xml.dom.minidom

__all__ = ["XMLBuilder"]

__doc__ = """
XMLBuilder is tiny library build on top of ElementTree.TreeBuilder to
make xml files creation more pythonomic. `XMLBuilder` use `with`
statement and attribute access to define xml document structure.

from __future__ import with_statement # only for python 2.5
from xmlbuilder import XMLBuilder

x = XMLBuilder('root')
x.some_tag
x.some_tag_with_data('text', a='12')

with x.some_tree(a='1'):
    with x.data:
        x.mmm
        for i in range(10):
            x.node(val=str(i))

etree_node = ~x # <= return xml.etree.ElementTree object
print str(x) # <= string object

will result:

<?xml version="1.0" encoding="utf-8" ?>
<root>
    <some_tag />
    <some_tag_with_data a="12">text</some_tag_with_data>
    <some_tree a="1">
        <data>
            <mmm />
            <node val="0" />
            <node val="1" />
            <node val="2" />
            <node val="3" />
            <node val="4" />
            <node val="5" />
            <node val="6" />
            <node val="7" />
            <node val="8" />
            <node val="9" />
        </data>
    </some_tree>
</root>

There some fields, which allow xml output customization:

formatted = produce formatted xml. default = True
tabstep   = tab string, used for formatting. default = ' ' * 4
encoding  = xml document encoding. default = 'utf-8'
xml_header = add xml header
                (<?xml version="1.0" encoding="$DOCUMENT_ENCODING$">)
            to begining of the document. default = True
builder = builder class, used for create dcument. Default =
                        xml.etree.ElementTree.TreeBuilder

Options can be readed by

x = XMLBuilder('root')
print x[option_name]

and changed by

x[option_name] = new_val

Happy xml'ing.
"""

class XMLNode:
    def __init__(self, doc, tag: str, *args, **kwargs) -> None:
        self._document = doc
        self._childs = []  # type: List[Union[str, 'XMLNode']]
        self._tag = tag
        self._attrs = {}  # type: Dict[str, str]
        self._xml_update(args, kwargs)

    def _xml_update(self, args: Tuple, kwargs: Dict[str, str]) -> None:
        for arg in args:
            if not isinstance(arg, (str, XMLNode)):
                raise ValueError(
                    "Non-named arguments should be string or XMLNode, not {!r}".format(arg.__class__))

        self._childs.extend(args)

        for key, val in kwargs.items():
            if not isinstance(val, str):
                raise ValueError("Attribute values should be string only, not {!r}".format(val.__class__))
            if not isinstance(key, str):
                raise ValueError("Attribute names should be string only, not {!r}".format(key.__class__))

        self._attrs.update(kwargs)

    def _debug(self, offset: str = "") -> None:
        print(offset + self._tag, " ".join("{}={!r}".format(k, v) for k, v in self._attrs.items()))

        for vl in self._childs:
            if isinstance(vl, str):
                print(offset + vl)
            else:
                vl._debug(offset + "    ")

    def _toxml(self, builder: Any) -> None:
        builder.start(self._tag, self._attrs)

        for child in self._childs:
            if isinstance(child, str):
                builder.data(child)
            else:
                child._toxml(builder)

        builder.end(self._tag)

    def __setitem__(self, name, val) -> None:
        self._xml_update(tuple(), {name: val})

    def __getattr__(self, name: str) -> 'XMLNode':
        if name.startswith('_ipython_'):
            raise AttributeError(name)
        node = XMLNode(self._document, name)
        self._childs.append(node)
        return node

    def __call__(self, *args, **kwargs) -> 'XMLNode':
        self._xml_update(args, kwargs)
        return self

    def __lshift__(self, val) -> 'XMLNode':
        self._xml_update((val,), {})
        return self

    def __enter__(self):
        return self._document()(self)

    def __exit__(self, x, y, z):
        self._document()(None)


class XMLBuilder:
    def __init__(self, root_name: str, *args, **kwargs) -> None:
        root = XMLNode(weakref.ref(self), root_name, *args, **kwargs)
        self._stack = [root]

    def __getattr__(self, name: str) -> XMLNode:
        if name.startswith('_ipython_'):
            raise AttributeError(name)
        return getattr(self._stack[-1], name)

    def __lshift__(self, val) -> XMLNode:
        return self._stack[-1] << val

    def __call__(self, obj: Optional[str]) -> 'XMLBuilder':
        if obj is None:
            self._stack.pop()
        else:
            self._stack.append(obj)
        return self

    def _debug(self):
        self._stack[0]._debug()


def tobytes(doc: XMLBuilder, encoding: str = "utf8", builder_cls: Any = TreeBuilder, pretty: bool = False) -> bytes:
    builder = builder_cls()
    doc._stack[0]._toxml(builder)
    res = tostring(builder.close(), encoding=encoding)
    if pretty:
        doc2 = xml.dom.minidom.parseString(res.decode(encoding))
        res = doc2.toprettyxml().encode(encoding)
    return res


def tostr(doc: XMLBuilder, encoding : str = "utf8", *args, **kwargs) -> str:
    return tobytes(doc, encoding, *args, **kwargs).decode(encoding)
