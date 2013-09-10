#!/usr/bin/env python

import pdfminer.pdfparser
import pdfminer.pdfinterp
import pdfminer.pdfdevice
import pdfminer.layout
import pdfminer.converter


class PDFDocument(object):
    """
    Wrapper to abstract away underlying PDF class. This is partly to simplify
    the concepts in the rest of the code to just the ones we need. And partly
    so we can, for example, change from PDFMiner to pdftoxml later if
    necessary.
    """

    @staticmethod
    def _initialise(fh):
        (doc, parser) = (pdfminer.pdfparser.PDFDocument(),
                         pdfminer.pdfparser.PDFParser(fh))

        parser.set_document(doc)
        doc.set_parser(parser)

        doc.initialize('')
        if not doc.is_extractable:
            raise ValueError(
                "pdfminer.pdfparser.PDFDocument is_extractable != True")
        la_params = pdfminer.layout.LAParams()
        la_params.word_margin = 0.0

        resource_manager = pdfminer.pdfinterp.PDFResourceManager()
        aggregator = pdfminer.converter.PDFPageAggregator(
            resource_manager, laparams=la_params)

        interpreter = pdfminer.pdfinterp.PDFPageInterpreter(
            resource_manager, aggregator)

        return doc, interpreter, aggregator

    def __init__(self, fh):
        self._pages = None

        (self._doc, self._interpreter, self._device) = self._initialise(fh)

    def __len__(self):
        return len(self.get_pages())

    def get_creator(self):
        return self._doc.info[0]['Creator']  # TODO: what's doc.info ?

    def get_pages(self):
        """
        Returns a list of lazy pages (parsed on demand)
        """
        if not self._pages:
            self._construct_pages()

        return self._pages

    def _construct_pages(self):
        self._pages = [PDFPage(self, page) for page in self._doc.get_pages()]


class PDFPage(object):
    """
    Lazy page processor.
    """

    def __init__(self, parent_pdf_document, page):
        assert isinstance(page, pdfminer.pdfparser.PDFPage), page.__class__

        self.pdf_document = parent_pdf_document
        self._page = page
        self._lt_page = None

    def lt_page(self):
        if not self._lt_page:
            self._parse_page()

        return self._lt_page

    def _parse_page(self):
        self.pdf_document._interpreter.process_page(self._page)
        self._lt_page = self.pdf_document._device.get_result()
        assert isinstance(self._lt_page,
                          pdfminer.layout.LTPage), self._lt_page.__class__