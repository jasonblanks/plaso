# -*- coding: utf-8 -*-
"""Tests for the Json2Csharp output class."""

import io
import sys
import unittest

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory

from plaso.lib import event
from plaso.lib import timelib
from plaso.output import json_4n6
from plaso.output import test_lib


class Json2CSharpTestEvent(event.EventObject):
  """Simplified EventObject for testing."""
  DATA_TYPE = 'test:json2csharp'

  def __init__(self):
    """Initialize event with data."""
    super(Json2CSharpTestEvent, self).__init__()
    self.timestamp = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01')
    self.hostname = u'ubuntu'
    self.display_name = u'OS: /var/log/syslog.1'
    self.inode = 12345678
    self.text = (
        u'Reporter <CRON> PID: |8442| (pam_unix(cron:session): session\n '
        u'closed for user root)')
    self.username = u'root'

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=u'/cases/image.dd')
    self.pathspec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TSK, inode=15, location=u'/var/log/syslog.1',
        parent=os_path_spec)


class Json2CSharpOutputTest(test_lib.OutputModuleTestCase):
  """Tests for the Json2CSharp outputter."""

  def setUp(self):
    """Sets up the objects needed for this test."""
    super(Json2CSharpOutputTest, self).setUp()
    self._output = io.BytesIO()
    self._formatter = json_4n6.Json2CSharpOutputFormatter(
        None, self._formatter_mediator, filehandle=self._output)
    self.event_object = Json2CSharpTestEvent()

  def testWriteHeaderAndfooter(self):
    """Tests the WriteHeader and WriteFooter functions."""
    expected_header = u'{"events": ['

    # based on the design footer will look as such below due to design.
    # expected_footer = u'{}]}'
    expected_footer = u'{"events": [{}]}'

    self._formatter.WriteHeader()

    header = self._output.getvalue()
    self.assertEqual(header, expected_header)

    self._formatter.WriteFooter()

    footer = self._output.getvalue()
    self.assertEqual(footer, expected_footer)

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    self._formatter.WriteEventBody(self.event_object)

    expected_uuid = self.event_object.uuid

    if sys.platform.startswith('win'):
      expected_os_location = u'C:\\\\cases\\image.dd'
    else:
      expected_os_location = u'\\/cases\\/image.dd'

    expected_os_location = expected_os_location.encode(u'utf-8')


    expected_event_body = (
        '{{"username": "root","display_name": "OS: '
        '\\/var\\/log\\/syslog.1","uuid": "{0:s}","data_type": '
        '"test:json2csharp",'
        '"timestamp": "2012-06-27 18:17:01+00:00","hostname": "ubuntu","text": '
        '"Reporter <CRON> PID: |8442| (pam_unix(cron:session): session\\\\n '
        'closed for user root)","TSKPathSpec_inode": 15,'
        '"TSKPathSpec_location": "\\/var\\/log\\/syslog.1",'
        '"OSPathSpec_location": "{1:s}","OSPathSpec_parent": '
        '"None","inode": 12345678}},\n').format(
            expected_uuid, expected_os_location)


    event_body = self._output.getvalue()
    self.assertEqual(event_body, expected_event_body)


if __name__ == '__main__':
  unittest.main()
