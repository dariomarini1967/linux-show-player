# -*- coding: utf-8 -*-
#
# This file is part of Linux Show Player
#
# Copyright 2012-2016 Francesco Ceruti <ceppofrancy@gmail.com>
#
# Linux Show Player is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Linux Show Player is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Linux Show Player.  If not, see <http://www.gnu.org/licenses/>.

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QLabel, QProgressBar

from lisp.core.signal import Connection
from lisp.cues.cue import CueNextAction, CueState
from lisp.cues.cue_time import CueTime, CueWaitTime
from lisp.utils.util import strtime


class CueStatusIcon(QLabel):
    EMPTY = QIcon()

    START = QIcon.fromTheme('media-playback-start')
    PAUSE = QIcon.fromTheme('media-playback-pause')
    ERROR = QIcon.fromTheme('dialog-error')

    SELECT = QIcon.fromTheme('mark-location')

    STYLESHEET = 'background: transparent; padding-left: 20px;'
    SIZE = 16

    def __init__(self, cue, *args):
        super().__init__(*args)
        self.setStyleSheet(CueStatusIcon.STYLESHEET)

        self.cue = cue
        self.cue.started.connect(self._start, Connection.QtQueued)
        self.cue.stopped.connect(self._stop, Connection.QtQueued)
        self.cue.paused.connect(self._pause, Connection.QtQueued)
        self.cue.error.connect(self._error, Connection.QtQueued)
        self.cue.end.connect(self._stop, Connection.QtQueued)

    def _start(self):
        self.setPixmap(self.START .pixmap(self.SIZE, self.SIZE))

    def _pause(self):
        self.setPixmap(self.PAUSE.pixmap(self.SIZE, self.SIZE))

    def _error(self, *args):
        self.setPixmap(self.ERROR.pixmap(self.SIZE, self.SIZE))

    def _stop(self):
        self.setPixmap(self.EMPTY.pixmap(self.SIZE, self.SIZE))

    def sizeHint(self):
        return QSize(self.SIZE, self.SIZE)


class NextActionIcon(QLabel):
    DO_NOTHING = QIcon()
    AUTO_NEXT = QIcon.fromTheme('auto-next')
    AUTO_FOLLOW = QIcon.fromTheme('auto-follow')

    STYLESHEET = 'background: transparent; padding-left: 1px'
    SIZE = 16

    def __init__(self, cue, *args):
        super().__init__(*args)
        self.setStyleSheet(self.STYLESHEET)

        self.cue = cue
        self.cue.changed('next_action').connect(self._update_icon, Connection.QtQueued)

        self._update_icon(self.cue.next_action)

    def _update_icon(self, next_action):
        next_action = CueNextAction(next_action)
        pixmap = self.DO_NOTHING.pixmap(self.SIZE, self.SIZE)

        if next_action == CueNextAction.AutoNext:
            pixmap = self.AUTO_NEXT.pixmap(self.SIZE, self.SIZE)
            self.setToolTip(CueNextAction.AutoNext.value)
        elif next_action == CueNextAction.AutoFollow:
            pixmap = self.AUTO_FOLLOW.pixmap(self.SIZE, self.SIZE)
            self.setToolTip(CueNextAction.AutoFollow.value)
        else:
            self.setToolTip('')

        self.setPixmap(pixmap)

    def sizeHint(self):
        return QSize(self.SIZE + 2, self.SIZE)


class TimeWidget(QProgressBar):

    def __init__(self, cue, *args):
        super().__init__(*args)
        self.setObjectName('ListTimeWidget')
        self.setValue(0)
        self.setTextVisible(True)

        self.show_zero_duration = False
        self.accurate_time = True
        self.cue = cue

    def _update_time(self, time):
        self.setValue(time)
        self.setFormat(strtime(time, accurate=self.accurate_time))

    def _update_duration(self, duration):
        if duration > 0 or self.show_zero_duration:
            # Display as disabled if duration < 0
            self.setEnabled(duration > 0)
            self.setTextVisible(True)
            self.setFormat(strtime(duration, accurate=self.accurate_time))
            # Avoid settings min and max to 0, or the the bar go in busy state
            self.setRange(0 if duration > 0 else -1, duration)
        else:
            self.setTextVisible(False)

    def _update_style(self, state):
        self.setProperty('state', state)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def _running(self):
        self._update_style('running')

    def _pause(self):
        self._update_style('pause')
        self._update_time(self.value())

    def _stop(self):
        self._update_style('stop')
        self.setValue(self.minimum())

    def _error(self):
        self._update_style('error')
        self.setValue(self.minimum())


class CueTimeWidget(TimeWidget):

    def __init__(self, cue, *args):
        super().__init__(cue, *args)

        self.cue.started.connect(self._running, Connection.QtQueued)
        self.cue.stopped.connect(self._stop, Connection.QtQueued)
        self.cue.paused.connect(self._pause, Connection.QtQueued)
        self.cue.error.connect(self._error, Connection.QtQueued)
        self.cue.end.connect(self._stop, Connection.QtQueued)
        self.cue.changed('duration').connect(self._update_duration,
                                             mode=Connection.QtQueued)

        self.cue_time = CueTime(self.cue)
        self.cue_time.notify.connect(self._update_time,
                                     mode=Connection.QtQueued)

        if cue.state == CueState.Running:
            self._running()
        elif cue.state == CueState.Pause:
            self._pause()
        elif cue.state == CueState.Error:
            self._error()
        else:
            self._stop()

    def _stop(self):
        super()._stop()
        self._update_duration(self.cue.duration)


class PreWaitWidget(TimeWidget):

    def __init__(self, cue, *args):
        super().__init__(cue, *args)
        self.show_zero_duration = True

        self.cue.pre_wait_enter.connect(self._running, Connection.QtQueued)
        self.cue.pre_wait_exit.connect(self._stop, Connection.QtQueued)
        self.cue.changed('pre_wait').connect(self._update_duration, Connection.QtQueued)

        self._update_duration(self.cue.pre_wait)

        self.wait_time = CueWaitTime(self.cue, mode=CueWaitTime.Mode.Pre)
        self.wait_time.notify.connect(self._update_time, Connection.QtQueued)

    def _update_duration(self, duration):
        # The wait time is in seconds, we need milliseconds
        super()._update_duration(duration * 1000)

    def _stop(self):
        super()._stop()
        self._update_duration(self.cue.pre_wait)


class PostWaitWidget(TimeWidget):

    def __init__(self, cue, *args):
        super().__init__(cue, *args)
        self.show_zero_duration = True

        self.cue.post_wait_exit.connect(self._stop, Connection.QtQueued)
        self.cue.end.connect(self._cue_stop, Connection.QtQueued)
        self.cue.stopped.connect(self._cue_stop, Connection.QtQueued)
        self.cue.error.connect(self._cue_stop, Connection.QtQueued)
        self.cue.changed('next_action').connect(self._next_action_changed, Connection.QtQueued)

        self.wait_time = CueWaitTime(self.cue, mode=CueWaitTime.Mode.Post)
        self.cue_time = CueTime(self.cue)

        self._next_action_changed(self.cue.next_action)

    def _update_duration(self, duration):
        if self.cue.next_action != CueNextAction.AutoFollow.value:
            # The wait time is in seconds, we need milliseconds
            duration *= 1000

        super()._update_duration(duration)

    def _next_action_changed(self, next_action):
        self.cue.started.disconnect(self._running)
        self.cue.post_wait_enter.disconnect(self._running)
        self.cue_time.notify.disconnect(self._update_time)
        self.wait_time.notify.disconnect(self._update_time)
        self.cue.changed('post_wait').disconnect(self._update_duration)
        self.cue.changed('duration').disconnect(self._update_duration)

        if next_action == CueNextAction.AutoFollow.value:
            self.cue.started.connect(self._running, Connection.QtQueued)
            self.cue_time.notify.connect(self._update_time, Connection.QtQueued)
            self.cue.changed('duration').connect(self._update_duration, Connection.QtQueued)
            self._update_duration(self.cue.duration)
        else:
            self.cue.post_wait_enter.connect(self._running, Connection.QtQueued)
            self.wait_time.notify.connect(self._update_time, Connection.QtQueued)
            self.cue.changed('post_wait').connect(self._update_duration, Connection.QtQueued)
            self._update_duration(self.cue.post_wait)

    def _cue_stop(self):
        if self.cue.next_action == CueNextAction.AutoFollow.value:
            self._stop()

    def _stop(self):
        super()._stop()

        if self.cue.next_action == CueNextAction.AutoFollow.value:
            self._update_duration(self.cue.duration)
        else:
            self._update_duration(self.cue.post_wait)