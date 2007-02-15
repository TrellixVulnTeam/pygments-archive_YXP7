# -*- coding: utf-8 -*-
"""
    pygments.formatters.html
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Formatter for HTML output.

    :copyright: 2006-2007 by Georg Brandl, Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import sys, os
import StringIO

from pygments.formatter import Formatter
from pygments.token import Token, Text, STANDARD_TYPES
from pygments.util import get_bool_opt, get_int_opt


__all__ = ['HtmlFormatter']


def escape_html(text):
    """Escape &, <, > as well as single and double quotes for HTML."""
    return text.replace('&', '&amp;').  \
                replace('<', '&lt;').   \
                replace('>', '&gt;').   \
                replace('"', '&quot;'). \
                replace("'", '&#39;')


def get_random_id():
    """Return a random id for javascript fields."""
    from random import random
    from time import time
    try:
        from hashlib import sha1 as sha
    except ImportError:
        import sha
        sha = sha.new
    return sha('%s|%s' % (random(), time())).hexdigest()


def _get_ttype_class(ttype):
    fname = STANDARD_TYPES.get(ttype)
    if fname:
        return fname
    aname = ''
    while fname is None:
        aname = '-' + ttype[-1] + aname
        ttype = ttype.parent
        fname = STANDARD_TYPES.get(ttype, '')
    return fname + aname


DOC_HEADER = '''\
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN"
   "http://www.w3.org/TR/html4/strict.dtd">

<html>
<head>
  <title>%(title)s</title>
  <meta http-equiv="content-type" content="text/html; charset=%(encoding)s">
  <style type="text/css">
td.linenos { background-color: #f0f0f0; padding-right: 10px; }
%(styledefs)s
  </style>
</head>
<body>
<h2>%(title)s</h2>

'''


DOC_HEADER_EXTERNALCSS = '''\
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN"
   "http://www.w3.org/TR/html4/strict.dtd">

<html>
<head>
  <title>%(title)s</title>
  <meta http-equiv="content-type" content="text/html; charset=%(encoding)s">
  <link rel="stylesheet" href="%(cssfile)s" type="text/css">
</head>
<body>
<h2>%(title)s</h2>

'''

DOC_FOOTER = '''\
</body>
</html>
'''


CSSFILE_TEMPLATE = '''\
td.linenos { background-color: #f0f0f0; padding-right: 10px; }
%(styledefs)s
'''


class HtmlFormatter(Formatter):
    r"""
    Format tokens as HTML 4 ``<span>`` tags within a ``<pre>`` tag, wrapped
    in a ``<div>`` tag. The ``<div>``'s CSS class can be set by the `cssclass`
    option.

    If the `linenos` option is given and true, the ``<pre>`` is additionally
    wrapped inside a ``<table>`` which has one row and two cells: one
    containing the line numbers and one containing the code. Example:

    .. sourcecode:: html

        <div class="highlight" >
        <table><tr>
          <td class="linenos" title="click to toggle"
            onclick="with (this.firstChild.style)
                     { display = (display == '') ? 'none' : '' }">
            <pre>1
            2</pre>
          </td>
          <td class="code">
            <pre><span class="Ke">def </span><span class="NaFu">foo</span>(bar):
              <span class="Ke">pass</span>
            </pre>
          </td>
        </tr></table></div>

    (whitespace added to improve clarity). Wrapping can be disabled using the
    `nowrap` option.

    With the `full` option, a complete HTML 4 document is output, including
    the style definitions inside a ``<style>`` tag, or in a separate file if
    the `cssfile` option is given.

    The `get_style_defs(arg='')` method of a `HtmlFormatter` returns a string
    containing CSS rules for the CSS classes used by the formatter. The
    argument `arg` can be used to specify additional CSS selectors that
    are prepended to the classes. A call `fmter.get_style_defs('td .code')`
    would result in the following CSS classes:

    .. sourcecode:: css

        td .code .kw { font-weight: bold; color: #00FF00 }
        td .code .cm { color: #999999 }
        ...

    If you have pygments 0.6 or higher you can also pass a list of tuple to the
    `get_style_defs` method to request multiple prefixes for the tokens:

    .. sourcecode:: python

        formatter.get_style_defs(['div.syntax pre', 'pre.syntax'])

    The output would then look like this:

    .. sourcecode:: css

        div.syntax pre .kw,
        pre.syntax .kw { font-weight: bold; color: #00FF00 }
        div.syntax pre .cm,
        pre.syntax .cm { color: #999999 }
        ...

    Additional options accepted:

    `nowrap`
        If set to ``True``, don't wrap the tokens at all, not even inside a ``<pre>``
        tag. This disables all other options (default: ``False``).

    `noclasses`
        If set to true, token ``<span>`` tags will not use CSS classes, but
        inline styles. This is not recommended for larger pieces of code since
        it increases output size by quite a bit (default: ``False``).

    `classprefix`
        Since the token types use relatively short class names, they may clash
        with some of your own class names. In this case you can use the
        `classprefix` option to give a string to prepend to all Pygments-generated
        CSS class names for token types.
        Note that this option also affects the output of `get_style_defs()`.

    `cssclass`
        CSS class for the wrapping ``<div>`` tag (default: ``'highlight'``).

    `cssstyles`
        Inline CSS styles for the wrapping ``<div>`` tag (default: ``''``).

    `cssfile`
        If the `full` option is true and this option is given, it must be the
        name of an external file. If the filename does not include an absolute
        path, the file's path will be assumed to be relative to the main output
        file's path, if the latter can be found. The stylesheet is then written
        to this file instead of the HTML file. *New in Pygments 0.6.*

    `linenospecial`
        If set to a number n > 0, every nth line number is given the CSS
        class ``"special"`` (default: ``0``).

    `nobackground`
        If set to ``True``, the formatter won't output the background color
        for the wrapping element (this automatically defaults to ``False``
        when there is no wrapping element [eg: no argument for the
        `get_syntax_defs` method given]) (default: ``False``). *New in
        Pygments 0.6.*

    `lineseparator`
        This string is output between lines of code. It defaults to ``"\n"``,
        which is enough to break a line inside ``<pre>`` tags, but you can
        e.g. set it to ``"<br>"`` to get HTML line breaks. *New in Pygments
        0.7.*


    **Subclassing the HTML formatter**

    *New in Pygments 0.7.*

    The HTML formatter is now built in a way that allows easy subclassing, thus
    customizing the output HTML code. The `format()` method calls
    `self._format_lines()` which returns a generator that yields tuples of ``(1,
    line)``, where the ``1`` indicates that the ``line`` is a line of the
    formatted source code.

    If the `nowrap` option is set, the generator is the iterated over and the
    resulting HTML is output.

    Otherwise, `format()` calls `self.wrap()`, which wraps the generator with
    other generators. These may add some HTML code to the one generated by
    `_format_lines()`, either by modifying the lines generated by the latter,
    then yielding them again with ``(1, line)``, and/or by yielding other HTML
    code before or after the lines, with ``(0, html)``. The distinction between
    source lines and other code makes it possible to wrap the generator multiple
    times.

    The default `wrap()` implementation adds a ``<div>`` and a ``<pre>`` tag.

    A custom `HtmlFormatter` subclass could look like this:

    .. sourcecode:: python

        class CodeHtmlFormatter(HtmlFormatter):

            def wrap(self, source, outfile):
                return self._wrap_code(source)

            def _wrap_code(self, source):
                yield 0, '<code>'
                for i, t in source:
                    if i == 1:
                        # it's a line of formatted code
                        t += '<br>'
                    yield i, t
                yield 0, '</code>'

    This results in wrapping the formatted lines with a ``<code>`` tag, where the
    source lines are broken using ``<br>`` tags.

    After calling `wrap()`, the `format()` method also adds the "line numbers"
    and/or "full document" wrappers if the respective options are set. Then, all
    HTML yielded by the wrapped generator is output.
    """

    name = 'HTML'
    aliases = ['html']
    filenames = ['*.html', '*.htm']

    def __init__(self, **options):
        Formatter.__init__(self, **options)
        self.nowrap = get_bool_opt(options, 'nowrap', False)
        self.noclasses = get_bool_opt(options, 'noclasses', False)
        self.classprefix = options.get('classprefix', '')
        self.cssclass = options.get('cssclass', 'highlight')
        self.cssstyles = options.get('cssstyles', '')
        self.cssfile = options.get('cssfile', '')
        self.linenos = get_bool_opt(options, 'linenos', False)
        self.linenostart = abs(get_int_opt(options, 'linenostart', 1))
        self.linenostep = abs(get_int_opt(options, 'linenostep', 1))
        self.linenospecial = abs(get_int_opt(options, 'linenospecial', 0))
        self.nobackground = get_bool_opt(options, 'nobackground', False)
        self.lineseparator = options.get('lineseparator', '\n')

        self._class_cache = {}
        self._create_stylesheet()

    def _get_css_class(self, ttype):
        """Return the css class of this token type prefixed with
        the classprefix option."""
        if ttype in self._class_cache:
            return self._class_cache[ttype]
        return self.classprefix + _get_ttype_class(ttype)

    def _create_stylesheet(self):
        t2c = self.ttype2class = {Token: ''}
        c2s = self.class2style = {}
        cp = self.classprefix
        for ttype, ndef in self.style:
            name = cp + _get_ttype_class(ttype)
            style = ''
            if ndef['color']:
                style += 'color: #%s; ' % ndef['color']
            if ndef['bold']:
                style += 'font-weight: bold; '
            if ndef['italic']:
                style += 'font-style: italic; '
            if ndef['underline']:
                style += 'text-decoration: underline; '
            if ndef['bgcolor']:
                style += 'background-color: #%s; ' % ndef['bgcolor']
            if ndef['border']:
                style += 'border: 1px solid #%s; ' % ndef['border']
            if style:
                t2c[ttype] = name
                # save len(ttype) to enable ordering the styles by
                # hierarchy (necessary for CSS cascading rules!)
                c2s[name] = (style[:-2], ttype, len(ttype))

    def get_style_defs(self, arg=''):
        """
        Return CSS style definitions for the classes produced by the
        current highlighting style. ``arg`` can be a string of selectors
        to insert before the token type classes.
        """
        if isinstance(arg, basestring):
            args = [arg]
        else:
            args = list(arg)

        def prefix(cls):
            tmp = []
            for arg in args:
                tmp.append((arg and arg + ' ' or '') + '.' + cls)
            return ', '.join(tmp)

        styles = [(level, ttype, cls, style)
                  for cls, (style, ttype, level) in self.class2style.iteritems()
                  if cls and style]
        styles.sort()
        lines = ['%s { %s } /* %s */' % (prefix(cls), style, repr(ttype)[6:])
                 for level, ttype, cls, style in styles]
        if arg and not self.nobackground and \
           self.style.background_color is not None:
            text_style = ''
            if Text in self.ttype2class:
                text_style = ' ' + self.class2style[self.ttype2class[Text]][0]
            lines.insert(0, '%s { background: %s;%s }' %
                         (arg, self.style.background_color, text_style))
        return '\n'.join(lines)

    def _wrap_full(self, inner, outfile):
        if self.cssfile:
            if os.path.isabs(self.cssfile):
                # it's an absolute filename
                cssfilename = self.cssfile
            else:
                try:
                    filename = outfile.name
                    if not filename or filename[0] == '<':
                        # pseudo files, e.g. name == '<fdopen>'
                        raise AttributeError
                    cssfilename = os.path.join(os.path.dirname(filename), self.cssfile)
                except AttributeError:
                    print >>sys.stderr, 'Note: Cannot determine output file name, ' \
                          'using current directory as base for the CSS file name'
                    cssfilename = self.cssfile
            # write CSS file
            try:
                cf = open(cssfilename, "w")
                cf.write(CSSFILE_TEMPLATE %
                         {'styledefs': self.get_style_defs('body')})
                cf.close()
            except IOError, err:
                err.strerror = 'Error writing CSS file: ' + err.strerror
                raise

            yield 0, (DOC_HEADER_EXTERNALCSS %
                      dict(title     = self.title,
                           cssfile   = self.cssfile,
                           encoding  = self.encoding))
        else:
            yield 0, (DOC_HEADER %
                      dict(title     = self.title,
                           styledefs = self.get_style_defs('body'),
                           encoding  = self.encoding))

        for t, line in inner:
            yield t, line
        yield 0, DOC_FOOTER

    def _wrap_linenos(self, inner):
        dummyoutfile = StringIO.StringIO()
        lncount = 0
        for t, line in inner:
            if t:
                lncount += 1
            dummyoutfile.write(line)

        fl = self.linenostart
        mw = len(str(lncount + fl - 1))
        sp = self.linenospecial
        st = self.linenostep
        if sp:
            ls = '\n'.join([(i%st == 0 and
                             (i%sp == 0 and '<span class="special">%*d</span>'
                              or '%*d') % (mw, i)
                             or '')
                            for i in range(fl, fl + lncount)])
        else:
            ls = '\n'.join([(i%st == 0 and ('%*d' % (mw, i)) or '')
                            for i in range(fl, fl + lncount)])

        yield 0, ('<table><tr><td class="linenos"><pre>' +
                  ls + '</pre></td><td class="code">')
        yield 0, dummyoutfile.getvalue()
        yield 0, '</td></tr></table>'

    def _wrap_div(self, inner):
        yield 0, ('<div' + (self.cssclass and ' class="%s"' % self.cssclass)
                  + (self.cssstyles and ' style="%s"' % self.cssstyles) + '>')
        for tup in inner:
            yield tup
        yield 0, '</div>\n'

    def _wrap_pre(self, inner):
        yield 0, '<pre>'
        for tup in inner:
            yield tup
        yield 0, '</pre>'

    def _format_lines(self, tokensource):
        """
        Just format the tokens, without any wrapping tags.
        Yield individual lines.
        """
        nocls = self.noclasses
        enc = self.encoding
        lsep = self.lineseparator
        # for <span style=""> lookup only
        getcls = self.ttype2class.get
        c2s = self.class2style

        lspan = ''
        line = ''
        for ttype, value in tokensource:
            if nocls:
                cclass = getcls(ttype)
                while cclass is None:
                    ttype = ttype.parent
                    cclass = getcls(ttype)
                cspan = cclass and '<span style="%s">' % c2s[cclass][0] or ''
            else:
                cls = self._get_css_class(ttype)
                cspan = cls and '<span class="%s">' % cls or ''

            if enc:
                value = value.encode(enc)

            parts = escape_html(value).split('\n')

            # for all but the last line
            for part in parts[:-1]:
                if line:
                    if lspan != cspan:
                        line += (lspan and '</span>') + cspan + part + \
                                (cspan and '</span>') + lsep
                    else: # both are the same
                        line += part + (lspan and '</span>') + lsep
                    yield 1, line
                    line = ''
                elif part:
                    yield 1, cspan + part + (cspan and '</span>') + lsep
                else:
                    yield 1, lsep
            # for the last line
            if line and parts[-1]:
                if lspan != cspan:
                    line += (lspan and '</span>') + cspan + parts[-1]
                    lspan = cspan
                else:
                    line += parts[-1]
            elif parts[-1]:
                line = cspan + parts[-1]
                lspan = cspan
            # else we neither have to open a new span nor set lspan

        if line:
            yield 1, line + (lspan and '</span>') + lsep

    def wrap(self, source, outfile):
        """
        Wrap the ``source``, which is a generator yielding
        individual lines, in custom generators. See docstring
        for `format`. Can be overridden.
        """
        return self._wrap_div(self._wrap_pre(source))

    def format(self, tokensource, outfile):
        """
        The formatting process uses several nested generators; which of
        them are used is determined by the user's options.

        Each generator should take at least one argument, ``inner``,
        and wrap the pieces of text generated by this.

        Always yield 2-tuples: (code, text). If "code" is 1, the text
        is part of the original tokensource being highlighted, if it's
        0, the text is some piece of wrapping. This makes it possible to
        use several different wrappers that process the original source
        linewise, e.g. line number generators.
        """
        source = self._format_lines(tokensource)
        if not self.nowrap:
            source = self.wrap(source, outfile)
            if self.linenos:
                source = self._wrap_linenos(source)
            if self.full:
                source = self._wrap_full(source, outfile)

        for t, piece in source:
            outfile.write(piece)
