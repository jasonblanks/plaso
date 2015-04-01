#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Parser for Linux Auth Logs.

Developed on Ubuntu 14.04 may work with other distros."""


import logging
import pyparsing
import re

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import mediator
from plaso.parsers import text_parser


__author__ = 'jason blanks (jason.blanks@gmail.com)'


class LinuxLogAuthEvent(time_events.TimestampEvent):
  """Convenience class for Linux Auth Log events."""

  DATA_TYPE = 'linux:auth'

  def __init__(self, timestamp, structure):
    """Initializes a Linux Auth Log Event.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of seconds since Jan 1, 1970 00:00:00 UTC.
      structure: Dict of elements from the auth log line.
    """
    super(LinuxLogAuthEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.ADDED_TIME)
    self.alert = structure.alert
    self.daemon = structure.daemon
    self.hostname = structure.hostname
    #self.pid = structure.pid
    self.pid = None
    self.timestamp = timestamp


class LinuxLogAuthParser(text_parser.PyparsingSingleLineTextParser):
  """Parse Linux Auth log files."""

  #pid = None
  NAME = u'linux_auth'
  DESCRIPTION = u'Parser for the linux Auth Log'

  MONTH = text_parser.PyparsingConstants.MONTH.setResultsName('month')
  DAY = text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName('day')
  TIME = text_parser.PyparsingConstants.TIME.setResultsName('time')
  HOSTNAME = pyparsing.Word(pyparsing.printables).setResultsName('hostname')
  # TODO:  1. Test for daemon meta, set if present.
  #           Test would be for more than one ':'
  DAEMON_DEFAULT = pyparsing.Word(pyparsing.alphanums+"-").setResultsName('daemon')
  DAEMON_PID = pyparsing.OneOrMore((
      pyparsing.Word(pyparsing.alphanums).setResultsName('daemon') +
      pyparsing.Regex(r'\[(.*?)\]').setResultsName('pid')))
  ALERT = pyparsing.restOfLine.setWhitespaceChars(': ').setResultsName('alert')

  LOG_LINE_PID = (MONTH + DAY + TIME + HOSTNAME + DAEMON_PID + ALERT)
  LOG_LINE_DEFAULT = (MONTH + DAY + TIME + HOSTNAME + DAEMON_DEFAULT + ALERT)


  LINE_STRUCTURES = [
      ('pidline', LOG_LINE_PID),
      ('logline', LOG_LINE_DEFAULT)]


  def GetTimestamp(self, structure, timezone):
    """Determines the timestamp from the pyparsing ParseResults.
       Year for testing is set to current year.  Generally the log
       files do not hold a year stamp as logs are generally
       rotated daily. A better method would probobly be to
       grab year from file creation date.  Looking for sugestions."""

    stats = self.file_entry.GetStat()
    try:
      year = timelib.Timestamp.CopyToDatetime(stats.ctime, timezone).strftime('%Y')
    except ValueError as exception:
      year = timelib.GetCurrentYear()
      logging.error((
        u'Unable to determine year of auth log file with ctime '
        u'\nDefaulting to current year '))
    structure.month = timelib.MONTH_DICT.get(structure.month.lower(), None)

    D = int(structure.day)
    Y = int(year)
    M = int(structure.month)
    h = int(structure.time[0])
    m = int(structure.time[1])
    s = int(structure.time[2])
    ms = int(0)
    timestamp = timelib.Timestamp.FromTimeParts(Y, M, D, h, m, s, ms)
    '''
    timestamp = timelib.Timestamp.FromTimeParts(int(year),
                                                int(structure.month),
                                                int(structure.day),
                                                int(structure.time[0]),
                                                int(structure.time[1]),
                                                int(structure.time[2]))
    try:
      timestamp = timelib.Timestamp.FromTimeParts(
          int(year, 10),
          int(structure.month, 10),
          int(structure.day, 10),
          int(structure.time[0], 10),
          int(structure.time[1], 10),
          int(structure.time[2], 10))
    except:
      logging.error((
        u'Unable to determine month from auth log file'))
    '''

    if not (structure.month and structure.day and structure.time):
      logging.warning(u'Unable to extract timestamp from auth logline.')
      return

    return timestamp

  def VerifyStructure(self, parser_mediator, line):
    authRegEx = re.compile(u'(auth\.log)|(auth\.log\.\d)|(auth.log\.\d\.gz)')
    loglocation = self.file_entry.path_spec.location

    if authRegEx.search(loglocation):
      return True

    else:
      return False

  def ParseRecord(self, parser_mediator, key, structure):
    """Parse each record structure and return an EventObject if apyparsinglicable.

    Args:
      parser_mediator: A parser mediator object (instance of ParserContext).
      key: An identification string indicating the name of the parsed
           structure.
      structure: A pyparsing.ParseResults object from a line in the
               log file.
    Returns:
      An event object (instance of EventObject) or None.
    """

    if key == 'logline':
      #test print statement, ignore, will be removed.
      #print 'loglne used'
      return self._ParseLogLine(structure, parser_mediator)
    elif key == 'pidline':
      return self._ParseLogLine(structure, parser_mediator)
    else:
      logging.warning(
          u'LinuxLogAuthParser, unknown structure.')

  def _ParseLogLine(self, structure, parser_mediator):
    """Gets an event_object or None from the pyparsing ParseResults.

    Args:
      structure: the pyparsing ParseResults object.
    Returns:
      event_object: a plaso event or None.
    """

    timestamp = self.GetTimestamp(structure, parser_mediator.timezone)

    return LinuxLogAuthEvent(timestamp, structure)


manager.ParsersManager.RegisterParser(LinuxLogAuthParser)
