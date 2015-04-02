# -*- coding: utf-8 -*-
"""
Output module for the json2csharp format.

The json2csharp format is used by http://json2csharp.com/. Note that
it differs from the JSON output module (json_out) in the
following manner:

json2csharp requires the events to be list:
events : [
{...},
]

where the JSON output module (json_out) defines events as a dictionary:

{
"event_0": {...},
}
"""


import logging
import sys
from types import NoneType

from plaso.lib import timelib
from plaso.output import interface
from plaso.output import manager


__author__ = 'jason blanks(jason.blanks@gmail.com)'


class Json2CSharpOutputFormatter(interface.FileOutputModule):
  """u'JSON output compatible with json2csharp.com.'"""

  NAME = u'json2csharp'
  DESCRIPTION = u'Saves as a flat JSON that validates with json2csharp.com.'

  def __init__(
      self, store, formatter_mediator, filehandle=sys.stdout, config=None,
      filter_use=None):
    """Initializes the output module object.

    Args:
      store: A storage file object (instance of StorageFile) that defines
             the storage.
      formatter_mediator: The formatter mediator object (instance of
                          FormatterMediator).
      filehandle: Optional file-like object that can be written to.
                  The default is sys.stdout.
      config: Optional configuration object, containing config information.
              The default is None.
      filter_use: Optional filter object (instance of FilterObject).
                  The default is None.
    """
    super(Json2CSharpOutputFormatter, self).__init__(
        store, formatter_mediator, filehandle=filehandle, config=config,
        filter_use=filter_use)
    self._event_counter = 0

  def _SanitizeEntry(self, entry):
    """Sanitize output to play nice with JSON."""

    if isinstance(entry, (str, unicode)):
      # Line feed, new line.
      entry = entry.replace(u'\n', u'\\n')
      # Carriage return.
      entry = entry.replace(u'\r', u'\\r')
      # Form feed.
      entry = entry.replace(u'\f', u'\\f')
      # Backspace.
      entry = entry.replace(u'\b', u'\\b')
      # Vertical tab.
      entry = entry.replace(u'\v', u'\\v')
      # Forward slash.
      entry = entry.replace(u'\\', u'\\\\')
      # Double quotes.
      entry = entry.replace(u'"', u'\\"')
      # Forward slash.
      entry = entry.replace(u'/', u'\\/')
      # Horizontal tab.
      entry = entry.replace(u'\t', u',')
    return entry

  def _Recurse(self, line, item, parent):
    # Test and properly handle based on value type.

    # Parent key check.
    if parent != None:
      parent = u'{0:s}_{1:s}'.format(parent, item[0])
    else:
      parent = unicode(item[0])

    if isinstance(item[1], (bool, NoneType)):
      line.append(u'"{0:s}": "{1!s}"'.format(parent, item[1]))

    elif isinstance(item[1], unicode):
      sanitized_item = self._SanitizeEntry(item[1])
      parent = self._SanitizeEntry(parent)
      line.append(u'"{0:s}": "{1:s}"'.format(parent, sanitized_item))

    elif isinstance(item[1], str):
      sanitized_item = self._SanitizeEntry(item[1])
      parent = self._SanitizeEntry(parent)
      line.append(u'"{0:s}": "{1:s}"'.format(parent, sanitized_item))

    elif isinstance(item[1], (int, long, float)):
      parent = self._SanitizeEntry(parent)

      # Convert timestamp to datetime.
      if unicode(item[0]) == u'timestamp':
        print vars(self)
        try:
          datetime_item = timelib.Timestamp.CopyToDatetime(
              item[1], self._timezone)
          line.append(u'"{0:s}": "{1!s}"'.format(parent, datetime_item))
        except ValueError:
          line.append(u'"{0:s}": "Bad Time Format"'.format(parent))
      else:
        line.append((
            u'"{0:s}": {1:d}'.format(parent, self._SanitizeEntry(item[1]))))


    elif isinstance(item[1], dict):
      parent = self._SanitizeEntry(parent)
      value_obj = item[1]
      for value in value_obj:
        # expecting unicode back, but just in case push it out to cycle
        # through.
        if not isinstance(value_obj[value], unicode):
          value = self._SanitizeEntry(value)
          if parent:
            parent = u'{0:s}_{1:s}'.format(parent, value)

          else:
            parent = u'{0:s}_{1:s}'.format(item[0], value)

          test = (parent, value_obj[value])
          self._Recurse(line, test, parent)

        else:
          temp_value = value_obj[value]
        if isinstance(value_obj[value], unicode):
          SanitizedTempValue = self._SanitizeEntry(temp_value)
          sanitize_value = self._SanitizeEntry(value)
          line.append(u'"{0:s}_{1:s}": "{2!s}"'.format(
              item[0], sanitize_value, SanitizedTempValue))

    # Check attribute value for list.
    elif isinstance(item[1], list):
      # For jsoncsharp we create one csv entry rather than a list object.
      temp_line = u'"{0:s}": "'.format(parent)
      list_count = 1
      if len(item[1]) == 0:
        temp_line = u'{0:s}None"'.format(temp_line)

      else:
        for entry in item[1]:
          if isinstance(entry, (basestring)):
            entry = self._SanitizeEntry(entry)

          if list_count == len(item[1]):
            temp_line = u'{0:s}{1!s}"'.format(temp_line, entry)
          else:
            temp_line = u'{0:s}{1!s}, '.format(temp_line, entry)
            list_count += 1

      line.append(temp_line)

    # isinstance in the case of class objects was not reliable, the
    # solution below seemed to work however.
    elif item[1].__class__.__class__:
      attributes = vars(item[1])
      for attribute in attributes.items():
        self._Recurse(line, attribute, unicode(item[1].__class__.__name__))

    else:
      # If ever made to this point alert to no match made.
      logging.warning(
          u'JsonCsharpOutput, unknown structure: %s.', item[1])
    return line

  def WriteHeader(self):
    """Writes the header to the output."""

    self._WriteLine(u'{"events": [')

  def WriteFooter(self):
    """Writes the footer to the output."""
    # Add a dummy event in the end that has no data in it.

    self._WriteLine(u'{}]}')

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output."""

    # Store reference to the originating object and create unique keys.
    parent = None

    # Defaults
    attributes = vars(event_object)
    self._WriteLine(u'{')
    lines = []

    for item in attributes.items():
      test_item = [item[0], item[1]]
      lines = self._Recurse(lines, test_item, parent)

    self._WriteLine(u','.join(lines))
    self._WriteLine(u'},\n')
    self._event_counter += 1


manager.OutputManager.RegisterOutput(Json2CSharpOutputFormatter)
