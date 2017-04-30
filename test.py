# Copyright 2017 Rich Lane
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import fcntl
import os
import select
import subprocess
import time
import unittest
import signal
import pty

BINARY = './shellhop'


def set_nonblocking(f):
    fd = f.fileno()
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)


def SpawnShellhop(argv):
    if isinstance(argv, str):
        argv = [argv]
    master, slave = pty.openpty()
    process = subprocess.Popen(
        [BINARY] + argv,
        stdin=slave,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    set_nonblocking(process.stdout)
    set_nonblocking(process.stderr)
    stdin = os.fdopen(master, 'w', 0)
    return process, stdin, process.stdout, process.stderr


BEGINNING_OF_LINE = '\x1b[G'
SAVE_CURSOR = '\x1b[s'
RESTORE_CURSOR = '\x1b[u'
HIDE_CURSOR = '\x1b[?25l'
SHOW_CURSOR = '\x1b[?25h'
REVERSE_VIDEO = '\x1b[7m'
UNDERLINE = '\x1b[4m'
NORMAL = '\x1b[0m'
CLEAR = '\x1b[J'


class ShellhopTest(unittest.TestCase):

    def expect(self, f, expected, timeout=1.0):
        actual = ''
        while len(actual) < len(expected):
            rfs, _, _ = select.select([f], [], [], timeout)
            if not rfs:
                break
            actual += f.read(len(expected))
        self.assertEquals(actual, expected)

    def expect_nothing(self, f, timeout=0.01):
        rfs, _, _ = select.select([f], [], [], timeout)
        if rfs:
            data = f.read()
            self.assertEquals(data, '')

    def test_basic(self):
        process, stdin, stdout, stderr = SpawnShellhop("abracadabra")
        self.expect(stderr, BEGINNING_OF_LINE)
        self.expect(stderr, SAVE_CURSOR)
        self.expect(stderr, HIDE_CURSOR)
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): abracadabra')
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Write one character, expect two matches.
        stdin.write('b')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): ')
        self.expect(stderr, 'a')
        self.expect(stderr, REVERSE_VIDEO)
        self.expect(stderr, 'b')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'racada')
        self.expect(stderr, UNDERLINE)
        self.expect(stderr, 'b')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'ra')
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Write two characters, expect redraws for each.
        stdin.write('ra')

        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): ')
        self.expect(stderr, 'a')
        self.expect(stderr, REVERSE_VIDEO)
        self.expect(stderr, 'br')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'acada')
        self.expect(stderr, UNDERLINE)
        self.expect(stderr, 'br')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'a')
        self.expect(stderr, CLEAR)

        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): ')
        self.expect(stderr, 'a')
        self.expect(stderr, REVERSE_VIDEO)
        self.expect(stderr, 'bra')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'cada')
        self.expect(stderr, UNDERLINE)
        self.expect(stderr, 'bra')
        self.expect(stderr, NORMAL)
        self.expect(stderr, CLEAR)

        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Write another character and get a unique match.
        stdin.write('c')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): ')
        self.expect(stderr, 'a')
        self.expect(stderr, REVERSE_VIDEO)
        self.expect(stderr, 'brac')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'adabra')
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Hit enter.
        stdin.write('\r')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, CLEAR)
        self.expect(stderr, SHOW_CURSOR)
        self.expect(stdout, '1\n')
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        self.assertEquals(process.wait(), 0)

    def test_backspace(self):
        process, stdin, stdout, stderr = SpawnShellhop("abc")
        self.expect(stderr, BEGINNING_OF_LINE)
        self.expect(stderr, SAVE_CURSOR)
        self.expect(stderr, HIDE_CURSOR)
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): abc')
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Hit backspace with no text.
        stdin.write('\x7f')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): ')
        self.expect(stderr, 'abc')
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Write a character.
        stdin.write('b')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): ')
        self.expect(stderr, 'a')
        self.expect(stderr, REVERSE_VIDEO)
        self.expect(stderr, 'b')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'c')
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Hit backspace.
        stdin.write('\x7f')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): ')
        self.expect(stderr, 'abc')
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Hit enter.
        stdin.write('\r')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, CLEAR)
        self.expect(stderr, SHOW_CURSOR)
        self.expect(stdout, '1\n')
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        self.assertEquals(process.wait(), 0)

    def test_empty_line(self):
        process, stdin, stdout, stderr = SpawnShellhop("abc")
        self.expect(stderr, BEGINNING_OF_LINE)
        self.expect(stderr, SAVE_CURSOR)
        self.expect(stderr, HIDE_CURSOR)
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): abc')
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Hit enter.
        stdin.write('\r')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, CLEAR)
        self.expect(stderr, SHOW_CURSOR)
        self.expect(stdout, '0\n')
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        self.assertEquals(process.wait(), 0)

    def test_nonmatching(self):
        process, stdin, stdout, stderr = SpawnShellhop("abc")
        self.expect(stderr, BEGINNING_OF_LINE)
        self.expect(stderr, SAVE_CURSOR)
        self.expect(stderr, HIDE_CURSOR)
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): abc')
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Write a nonmatching character. It should be ignored.
        stdin.write('d')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): ')
        self.expect(stderr, 'abc')
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Write a matching character.
        stdin.write('b')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): ')
        self.expect(stderr, 'a')
        self.expect(stderr, REVERSE_VIDEO)
        self.expect(stderr, 'b')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'c')
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Write a nonmatching character. It should be ignored.
        stdin.write('e')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): ')
        self.expect(stderr, 'a')
        self.expect(stderr, REVERSE_VIDEO)
        self.expect(stderr, 'b')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'c')
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Write a matching character.
        stdin.write('c')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): ')
        self.expect(stderr, 'a')
        self.expect(stderr, REVERSE_VIDEO)
        self.expect(stderr, 'bc')
        self.expect(stderr, NORMAL)
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Hit enter.
        stdin.write('\r')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, CLEAR)
        self.expect(stderr, SHOW_CURSOR)
        self.expect(stdout, '1\n')
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        self.assertEquals(process.wait(), 0)

    def test_next_prev(self):
        process, stdin, stdout, stderr = SpawnShellhop("abcabcabc")
        self.expect(stderr, BEGINNING_OF_LINE)
        self.expect(stderr, SAVE_CURSOR)
        self.expect(stderr, HIDE_CURSOR)
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): abcabcabc')
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Write a matching character.
        stdin.write('b')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): ')
        self.expect(stderr, 'a')
        self.expect(stderr, REVERSE_VIDEO)
        self.expect(stderr, 'b')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'ca')
        self.expect(stderr, UNDERLINE)
        self.expect(stderr, 'b')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'ca')
        self.expect(stderr, UNDERLINE)
        self.expect(stderr, 'b')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'c')
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Write a matching character.
        stdin.write('c')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): ')
        self.expect(stderr, 'a')
        self.expect(stderr, REVERSE_VIDEO)
        self.expect(stderr, 'bc')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'a')
        self.expect(stderr, UNDERLINE)
        self.expect(stderr, 'bc')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'a')
        self.expect(stderr, UNDERLINE)
        self.expect(stderr, 'bc')
        self.expect(stderr, NORMAL)
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Hit ctrl-N to move to second match.
        stdin.write('\x0e')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): ')
        self.expect(stderr, 'a')
        self.expect(stderr, UNDERLINE)
        self.expect(stderr, 'bc')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'a')
        self.expect(stderr, REVERSE_VIDEO)
        self.expect(stderr, 'bc')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'a')
        self.expect(stderr, UNDERLINE)
        self.expect(stderr, 'bc')
        self.expect(stderr, NORMAL)
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Hit ctrl-N to move to third match.
        stdin.write('\x0e')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): ')
        self.expect(stderr, 'a')
        self.expect(stderr, UNDERLINE)
        self.expect(stderr, 'bc')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'a')
        self.expect(stderr, UNDERLINE)
        self.expect(stderr, 'bc')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'a')
        self.expect(stderr, REVERSE_VIDEO)
        self.expect(stderr, 'bc')
        self.expect(stderr, NORMAL)
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Hit ctrl-N to move to first match.
        stdin.write('\x0e')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): ')
        self.expect(stderr, 'a')
        self.expect(stderr, REVERSE_VIDEO)
        self.expect(stderr, 'bc')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'a')
        self.expect(stderr, UNDERLINE)
        self.expect(stderr, 'bc')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'a')
        self.expect(stderr, UNDERLINE)
        self.expect(stderr, 'bc')
        self.expect(stderr, NORMAL)
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Hit ctrl-P to move to third match.
        stdin.write('\x10')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): ')
        self.expect(stderr, 'a')
        self.expect(stderr, UNDERLINE)
        self.expect(stderr, 'bc')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'a')
        self.expect(stderr, UNDERLINE)
        self.expect(stderr, 'bc')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'a')
        self.expect(stderr, REVERSE_VIDEO)
        self.expect(stderr, 'bc')
        self.expect(stderr, NORMAL)
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Hit ctrl-P to move to second match.
        stdin.write('\x10')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): ')
        self.expect(stderr, 'a')
        self.expect(stderr, UNDERLINE)
        self.expect(stderr, 'bc')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'a')
        self.expect(stderr, REVERSE_VIDEO)
        self.expect(stderr, 'bc')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'a')
        self.expect(stderr, UNDERLINE)
        self.expect(stderr, 'bc')
        self.expect(stderr, NORMAL)
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Hit enter.
        stdin.write('\r')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, CLEAR)
        self.expect(stderr, SHOW_CURSOR)
        self.expect(stdout, '4\n')
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        self.assertEquals(process.wait(), 0)

    def test_sigint(self):
        process, stdin, stdout, stderr = SpawnShellhop("abc")
        self.expect(stderr, BEGINNING_OF_LINE)
        self.expect(stderr, SAVE_CURSOR)
        self.expect(stderr, HIDE_CURSOR)
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): abc')
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        os.kill(process.pid, signal.SIGINT)
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, CLEAR)
        self.expect(stderr, SHOW_CURSOR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)
        self.assertEquals(process.wait(), -signal.SIGINT)

    def test_escape(self):
        process, stdin, stdout, stderr = SpawnShellhop("abc")
        self.expect(stderr, BEGINNING_OF_LINE)
        self.expect(stderr, SAVE_CURSOR)
        self.expect(stderr, HIDE_CURSOR)
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): abc')
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Write a matching character.
        stdin.write('b')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): ')
        self.expect(stderr, 'a')
        self.expect(stderr, REVERSE_VIDEO)
        self.expect(stderr, 'b')
        self.expect(stderr, NORMAL)
        self.expect(stderr, 'c')
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Hit escape.
        stdin.write('\x1b')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, CLEAR)
        self.expect(stderr, SHOW_CURSOR)
        self.expect(stdout, "0\n")
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

    def test_bash_source(self):
        script = r"""
function _shellhop {
  READLINE_POINT=$(./shellhop "$READLINE_LINE");
};
bind '"\C-xS0":beginning-of-line';
bind -x '"\C-xS1":"_shellhop"';
bind '"\C-x\C-f":"\C-xS0\C-xS1"';
"""[1:]

        process, stdin, stdout, stderr = SpawnShellhop("-b")
        self.expect(stdout, script)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)
        self.assertEquals(process.wait(), 0)

        process, stdin, stdout, stderr = SpawnShellhop("--bash")
        self.expect(stdout, script)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)
        self.assertEquals(process.wait(), 0)

    def test_bash_source_with_key(self):
        script = r"""
function _shellhop {
  READLINE_POINT=$(./shellhop "$READLINE_LINE");
};
bind '"\C-xS0":beginning-of-line';
bind -x '"\C-xS1":"_shellhop"';
bind '"\C-j":"\C-xS0\C-xS1"';
"""[1:]

        process, stdin, stdout, stderr = SpawnShellhop(["-b", "-k", "\\C-j"])
        self.expect(stdout, script)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)
        self.assertEquals(process.wait(), 0)

        process, stdin, stdout, stderr = SpawnShellhop(["--bash", "--key", "\\C-j"])
        self.expect(stdout, script)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)
        self.assertEquals(process.wait(), 0)

    def test_zsh_source(self):
        script = r"""
function _shellhop {
  CURSOR=$(./shellhop "$BUFFER" </dev/tty);
  zle redisplay;
};
zle -N shellhop _shellhop;
bindkey '\C-x\C-f' shellhop;
"""[1:]

        process, stdin, stdout, stderr = SpawnShellhop("-z")
        self.expect(stdout, script)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)
        self.assertEquals(process.wait(), 0)

        process, stdin, stdout, stderr = SpawnShellhop("--zsh")
        self.expect(stdout, script)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)
        self.assertEquals(process.wait(), 0)

    def test_zsh_source_with_key(self):
        script = r"""
function _shellhop {
  CURSOR=$(./shellhop "$BUFFER" </dev/tty);
  zle redisplay;
};
zle -N shellhop _shellhop;
bindkey '\C-j' shellhop;
"""[1:]

        process, stdin, stdout, stderr = SpawnShellhop(["-z", "-k", "\\C-j"])
        self.expect(stdout, script)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)
        self.assertEquals(process.wait(), 0)

        process, stdin, stdout, stderr = SpawnShellhop(["--zsh", "--key", "\\C-j"])
        self.expect(stdout, script)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)
        self.assertEquals(process.wait(), 0)

    def test_help(self):
        help_text = """\
usage: ./shellhop [OPTION]... LINE

Do an incremental search on the given line and write the index of the first
match to stdout.

  -b, --bash     output Bash shell commands to stdout
  -z, --zsh      output Zsh shell commands to stdout
  -k, --key=KEY  specify a key for --bash and --zsh
  -h, --help     display this help and exit
"""

        process, stdin, stdout, stderr = SpawnShellhop("-h")
        self.expect(stderr, help_text)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)
        self.assertEquals(process.wait(), 0)

        process, stdin, stdout, stderr = SpawnShellhop("--help")
        self.expect(stderr, help_text)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)
        self.assertEquals(process.wait(), 0)

if __name__ == "__main__":
    unittest.main()
