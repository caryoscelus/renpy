# Copyright 2004-2014 Tom Rothamel <pytom@bishoujo.us>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import sys
import os
import renpy
import subprocess

class TTSRoot(Exception):
    """
    An exception that can be used to cause the TTS system to read the text
    of the root displayable, rather than text of the currently focused
    displayable.
    """

# The root of the scene.
root = None

# The text of the last displayable.
last = ""

# A queue of things to say.
queue = [ ]

# The speech synthesis process.
process = None

def periodic():
    global process

    if process is not None:
        if process.poll() is not None:
            process = None

def speak_queued():
    """
    Speaks the queued messages, if any, using an os-specific method.
    """

    global process
    global queue

    # Stop the existing process.
    if process is not None:
        try:
            process.terminate()
            process.wait()
        except:
            pass

    process = None

    s = " ".join(queue).strip()

    if not s:
        return


    if renpy.linux:
        process = subprocess.Popen([ "espeak", s.encode("utf-8") ])
    elif renpy.macintosh:
        process = subprocess.Popen([ "say", renpy.exports.fsencode(s) ])
    elif renpy.windows:
        say_vbs = os.path.join(os.path.dirname(sys.executable), "say.vbs")
        process = subprocess.Popen([ "wscript", renpy.exports.fsencode(say_vbs), renpy.exports.fsencode(s) ])


    queue = [ ]


def speak(s, translate=True, force=False):
    """
    This is called by the system to queue the speaking of message `s`.
    """

    if not force and not renpy.game.preferences.self_voicing:
        return

    if translate:
        s = renpy.translation.translate_string(s)

    queue.append(s)


def set_root(d):
    global root
    root = d

# The old value of the self_voicing preference.
old_self_voicing = False

def displayable(d):
    """
    Causes the TTS system to read the text of the displayable `d`.
    """

    global old_self_voicing

    self_voicing = renpy.game.preferences.self_voicing

    if not self_voicing:
        if old_self_voicing:
            old_self_voicing = self_voicing
            speak("Self-voicing disabled.", force=True)
            speak_queued()

        return

    if not old_self_voicing:
        old_self_voicing = self_voicing
        speak("Self-voicing enabled.")


    global last

    if d is None:
        d = root

    while True:
        try:
            s = d._tts_all()
            break
        except TTSRoot:
            if d is root:
                return
            else:
                d = root

    global last

    if s != last:
        last = s
        speak(s, translate=False)

    speak_queued()