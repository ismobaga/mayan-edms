# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ValidationError

from mayan.apps.common.tests import BaseTestCase
from mayan.apps.documents.models import DocumentType
from mayan.apps.documents.tests import (
    DocumentTestMixin, TEST_DOCUMENT_TYPE_2_LABEL
)

from ..models import DocumentMetadata

from .literals import (
    TEST_DEFAULT_VALUE, TEST_LOOKUP_TEMPLATE, TEST_INCORRECT_LOOKUP_VALUE,
    TEST_CORRECT_LOOKUP_VALUE, TEST_DATE_VALIDATOR, TEST_DATE_PARSER,
    TEST_INVALID_DATE, TEST_VALID_DATE, TEST_PARSED_VALID_DATE
)
from .mixins import MetadataTypeTestMixin


class MetadataTestCase(DocumentTestMixin, MetadataTypeTestMixin, BaseTestCase):
    def setUp(self):
        super(MetadataTestCase, self).setUp()
        self._create_test_metadata_type()
        self.test_document_type.metadata.create(
            metadata_type=self.test_metadata_type
        )

    def test_no_default(self):
        document_metadata = DocumentMetadata(
            document=self.test_document, metadata_type=self.test_metadata_type
        )

        document_metadata.full_clean()
        document_metadata.save()

        self.assertEqual(
            getattr(
                self.test_document.metadata_value_of,
                self.test_metadata_type.name
            ), None
        )

    def test_default(self):
        self.test_metadata_type.default = TEST_DEFAULT_VALUE
        self.test_metadata_type.save()

        document_metadata = DocumentMetadata(
            document=self.test_document, metadata_type=self.test_metadata_type
        )

        document_metadata.full_clean()
        document_metadata.save()

        self.assertEqual(
            getattr(
                self.test_document.metadata_value_of,
                self.test_metadata_type.name
            ), TEST_DEFAULT_VALUE
        )

    def test_lookup_with_incorrect_value(self):
        self.test_metadata_type.lookup = TEST_LOOKUP_TEMPLATE
        self.test_metadata_type.save()

        document_metadata = DocumentMetadata(
            document=self.test_document, metadata_type=self.test_metadata_type,
            value=TEST_INCORRECT_LOOKUP_VALUE
        )

        with self.assertRaises(ValidationError):
            # Should return error
            document_metadata.full_clean()
            document_metadata.save()

    def test_lookup_with_correct_value(self):
        self.test_metadata_type.lookup = TEST_LOOKUP_TEMPLATE
        self.test_metadata_type.save()

        document_metadata = DocumentMetadata(
            document=self.test_document, metadata_type=self.test_metadata_type,
            value=TEST_CORRECT_LOOKUP_VALUE
        )

        document_metadata.full_clean()
        document_metadata.save()

        self.assertEqual(
            getattr(
                self.test_document.metadata_value_of,
                self.test_metadata_type.name
            ), TEST_CORRECT_LOOKUP_VALUE
        )

    def test_empty_optional_lookup(self):
        """
        Checks for GitLab issue #250
        Empty optional lookup metadata trigger validation error
        """
        self.test_metadata_type.lookup = TEST_LOOKUP_TEMPLATE
        self.test_metadata_type.save()

        document_metadata = DocumentMetadata(
            document=self.test_document, metadata_type=self.test_metadata_type
        )

        document_metadata.full_clean()
        document_metadata.save()

    def test_validation(self):
        self.test_metadata_type.validation = TEST_DATE_VALIDATOR

        document_metadata = DocumentMetadata(
            document=self.test_document, metadata_type=self.test_metadata_type,
            value=TEST_INVALID_DATE
        )

        with self.assertRaises(ValidationError):
            # Should return error
            document_metadata.full_clean()
            document_metadata.save()

        # Should not return error
        document_metadata.value = TEST_VALID_DATE
        document_metadata.full_clean()
        document_metadata.save()

        self.assertEqual(
            getattr(
                self.test_document.metadata_value_of,
                self.test_metadata_type.name
            ), TEST_VALID_DATE
        )

    def test_parsing(self):
        self.test_metadata_type.parser = TEST_DATE_PARSER

        document_metadata = DocumentMetadata(
            document=self.test_document, metadata_type=self.test_metadata_type,
            value=TEST_INVALID_DATE
        )

        with self.assertRaises(ValidationError):
            # Should return error
            document_metadata.full_clean()
            document_metadata.save()

        # Should not return error
        document_metadata.value = TEST_VALID_DATE
        document_metadata.full_clean()
        document_metadata.save()

        self.assertEqual(
            getattr(
                self.test_document.metadata_value_of,
                self.test_metadata_type.name
            ), TEST_PARSED_VALID_DATE
        )

    def test_required_metadata(self):
        self.test_document_type.metadata.all().delete()

        self.assertFalse(
            self.test_metadata_type.get_required_for(self.test_document_type)
        )

        self.test_document_type.metadata.create(
            metadata_type=self.test_metadata_type, required=False
        )

        self.assertFalse(
            self.test_metadata_type.get_required_for(self.test_document_type)
        )

        self.test_document_type.metadata.all().delete()

        self.test_document_type.metadata.create(
            metadata_type=self.test_metadata_type, required=True
        )

        self.assertTrue(
            self.test_metadata_type.get_required_for(self.test_document_type)
        )

    def test_unicode_lookup(self):
        # Should NOT return a ValidationError, otherwise test fails
        self.test_metadata_type.lookup = '??????1,??????2,test1,test2'
        self.test_metadata_type.save()
        self.test_metadata_type.validate_value(document_type=None, value='??????1')

    def test_non_unicode_lookup(self):
        # Should NOT return a ValidationError, otherwise test fails
        self.test_metadata_type.lookup = 'test1,test2'
        self.test_metadata_type.save()
        self.test_metadata_type.validate_value(document_type=None, value='test1')

    def test_add_new_metadata_type_on_document_type_change(self):
        """
        When switching document types, add the required metadata of the new
        document type, the value to the default of the metadata type.
        """
        self.test_metadata_type.default = TEST_DEFAULT_VALUE
        self.test_metadata_type.save()

        self.test_document_type_2 = DocumentType.objects.create(
            label=TEST_DOCUMENT_TYPE_2_LABEL
        )

        self.test_document_type_2.metadata.create(
            metadata_type=self.test_metadata_type, required=True
        )

        self.test_document.set_document_type(document_type=self.test_document_type_2)

        self.assertEqual(self.test_document.metadata.count(), 1)
        self.assertEqual(
            self.test_document.metadata.first().value, TEST_DEFAULT_VALUE
        )

    def test_preserve_metadata_value_on_document_type_change(self):
        """
        Preserve the document metadata that is present in the
        old and new document types
        """
        document_metadata = DocumentMetadata(
            document=self.test_document, metadata_type=self.test_metadata_type,
            value=TEST_DEFAULT_VALUE
        )

        document_metadata.full_clean()
        document_metadata.save()

        self.test_document_type_2 = DocumentType.objects.create(
            label=TEST_DOCUMENT_TYPE_2_LABEL
        )

        self.test_document_type_2.metadata.create(metadata_type=self.test_metadata_type)

        self.test_document.set_document_type(document_type=self.test_document_type_2)

        self.assertEqual(self.test_document.metadata.count(), 1)
        self.assertEqual(
            self.test_document.metadata.first().value, TEST_DEFAULT_VALUE
        )
        self.assertEqual(
            self.test_document.metadata.first().metadata_type, self.test_metadata_type
        )

    def test_delete_metadata_value_on_document_type_change(self):
        """
        Delete the old document metadata whose types are not present in the
        new document type
        """
        document_metadata = DocumentMetadata(
            document=self.test_document, metadata_type=self.test_metadata_type,
            value=TEST_DEFAULT_VALUE
        )

        document_metadata.full_clean()
        document_metadata.save()

        self.test_document_type_2 = DocumentType.objects.create(
            label=TEST_DOCUMENT_TYPE_2_LABEL
        )

        self.test_document.set_document_type(document_type=self.test_document_type_2)

        self.assertEqual(self.test_document.metadata.count(), 0)

    def test_duplicate_metadata_value_on_document_type_change(self):
        """
        Delete the old document metadata whose types are not present in the
        new document type
        """
        document_metadata = DocumentMetadata(
            document=self.test_document, metadata_type=self.test_metadata_type,
            value=TEST_DEFAULT_VALUE
        )

        document_metadata.full_clean()
        document_metadata.save()

        self.test_document_type_2 = DocumentType.objects.create(
            label=TEST_DOCUMENT_TYPE_2_LABEL
        )

        self.test_document_type_2.metadata.create(
            metadata_type=self.test_metadata_type, required=True
        )

        self.test_document.set_document_type(document_type=self.test_document_type_2)

        self.assertEqual(self.test_document.metadata.count(), 1)
        self.assertEqual(
            self.test_document.metadata.first().value, TEST_DEFAULT_VALUE
        )
        self.assertEqual(
            self.test_document.metadata.first().metadata_type, self.test_metadata_type
        )
