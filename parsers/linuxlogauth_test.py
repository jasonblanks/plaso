#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2015 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for the Linux Auth Log parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import linuxlogauth as linuxlogauth_formatter
from plaso.lib import eventdata
from plaso.parsers import linuxlogauth
from plaso.parsers import test_lib


class LinuxLogAuthUnitTest(test_lib.ParserTestCase):
  """Tests for the Linux Auth Log parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = linuxlogauth.LinuxLogAuthParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['linuxlogauth.log'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The file contains 22 lines which results in 22 event objects.
    self.assertEquals(len(event_objects), 22)

    event_object = event_objects[0]

    #self.assertEquals(event_object.timestamp, 1446038512000000)
    self.assertEquals(event_object.timestamp, 25968112000000)
    self.assertEquals(event_object.hostname, u'Eeeeek')
    self.assertEquals(event_object.daemon, u'kernel')
    self.assertEquals(event_object.pid, None)
    self.assertEquals(
        event_object.alert,
        u'[   19.837811] systemd-logind[936]: New seat seat0.')

    expected_msg = (
        u'hostname: Eeeeek daemon: kernel pid: None '
        u'alert: [   19.837811] systemd-logind[936]: New seat seat0.')
    expected_msg_short = (
        u'kernel '
        u'[   19.837811] systemd-logind[936]: New seat seat0.')

    # This is a shorthand test to extract the message strings
    # from the event object and to make sure that they match the
    # expected strings.
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
