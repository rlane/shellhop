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


def SpawnShellhop(line):
    master, slave = pty.openpty()
    process = subprocess.Popen(
        [BINARY, line],
        stdin=slave,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    set_nonblocking(process.stdout)
    set_nonblocking(process.stderr)
    return process, os.fdopen(master, 'w', 0)


SAVE_CURSOR = '\x1b[s'
RESTORE_CURSOR = '\x1b[u'
HIDE_CURSOR = '\x1b[?25l'
SHOW_CURSOR = '\x1b[?25h'
REVERSE_VIDEO = '\x1b[7m'
NORMAL = '\x1b[0m'
CLEAR = '\x1b[J'


class ShellhopTest(unittest.TestCase):

    def expect(self, f, expected, timeout=1.0):
        rfs, _, _ = select.select([f], [], [], timeout)
        self.assertEqual(rfs, [f])
        actual = f.read(len(expected))
        self.assertEquals(actual, expected)

    def expect_nothing(self, f, timeout=0.01):
        rfs, _, _ = select.select([f], [], [], timeout)
        if rfs:
            data = f.read()
            self.assertEquals(data, '')

    def test_basic(self):
        process, master = SpawnShellhop("abracadabra")
        self.expect(process.stderr, SAVE_CURSOR)
        self.expect(process.stderr, HIDE_CURSOR)
        self.expect(process.stderr, RESTORE_CURSOR)
        self.expect(process.stderr, '(shellhop): abracadabra')
        self.expect(process.stderr, CLEAR)
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

        # Write one character, expect two matches.
        master.write('b')
        self.expect(process.stderr, RESTORE_CURSOR)
        self.expect(process.stderr, '(shellhop): ')
        self.expect(process.stderr, 'a')
        self.expect(process.stderr, REVERSE_VIDEO)
        self.expect(process.stderr, 'b')
        self.expect(process.stderr, NORMAL)
        self.expect(process.stderr, 'racada')
        self.expect(process.stderr, REVERSE_VIDEO)
        self.expect(process.stderr, 'b')
        self.expect(process.stderr, NORMAL)
        self.expect(process.stderr, 'ra')
        self.expect(process.stderr, CLEAR)
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

        # Write two characters, expect redraws for each.
        master.write('ra')

        self.expect(process.stderr, RESTORE_CURSOR)
        self.expect(process.stderr, '(shellhop): ')
        self.expect(process.stderr, 'a')
        self.expect(process.stderr, REVERSE_VIDEO)
        self.expect(process.stderr, 'br')
        self.expect(process.stderr, NORMAL)
        self.expect(process.stderr, 'acada')
        self.expect(process.stderr, REVERSE_VIDEO)
        self.expect(process.stderr, 'br')
        self.expect(process.stderr, NORMAL)
        self.expect(process.stderr, 'a')
        self.expect(process.stderr, CLEAR)

        self.expect(process.stderr, RESTORE_CURSOR)
        self.expect(process.stderr, '(shellhop): ')
        self.expect(process.stderr, 'a')
        self.expect(process.stderr, REVERSE_VIDEO)
        self.expect(process.stderr, 'bra')
        self.expect(process.stderr, NORMAL)
        self.expect(process.stderr, 'cada')
        self.expect(process.stderr, REVERSE_VIDEO)
        self.expect(process.stderr, 'bra')
        self.expect(process.stderr, CLEAR)

        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

        # Write another character and get a unique match.
        master.write('c')
        self.expect(process.stderr, RESTORE_CURSOR)
        self.expect(process.stderr, '(shellhop): ')
        self.expect(process.stderr, 'a')
        self.expect(process.stderr, REVERSE_VIDEO)
        self.expect(process.stderr, 'brac')
        self.expect(process.stderr, NORMAL)
        self.expect(process.stderr, 'adabra')
        self.expect(process.stderr, CLEAR)
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

        # Hit enter.
        master.write('\r')
        self.expect(process.stderr, RESTORE_CURSOR)
        self.expect(process.stderr, CLEAR)
        self.expect(process.stderr, SHOW_CURSOR)
        self.expect(process.stdout, '1\n')
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

    def test_delete(self):
        process, master = SpawnShellhop("abc")
        self.expect(process.stderr, SAVE_CURSOR)
        self.expect(process.stderr, HIDE_CURSOR)
        self.expect(process.stderr, RESTORE_CURSOR)
        self.expect(process.stderr, '(shellhop): abc')
        self.expect(process.stderr, CLEAR)
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

        # Hit delete with no text.
        master.write('\x7f')
        self.expect(process.stderr, RESTORE_CURSOR)
        self.expect(process.stderr, '(shellhop): ')
        self.expect(process.stderr, 'abc')
        self.expect(process.stderr, CLEAR)
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

        # Write a character.
        master.write('b')
        self.expect(process.stderr, RESTORE_CURSOR)
        self.expect(process.stderr, '(shellhop): ')
        self.expect(process.stderr, 'a')
        self.expect(process.stderr, REVERSE_VIDEO)
        self.expect(process.stderr, 'b')
        self.expect(process.stderr, NORMAL)
        self.expect(process.stderr, 'c')
        self.expect(process.stderr, CLEAR)
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

        # Hit delete.
        master.write('\x7f')
        self.expect(process.stderr, RESTORE_CURSOR)
        self.expect(process.stderr, '(shellhop): ')
        self.expect(process.stderr, 'abc')
        self.expect(process.stderr, CLEAR)
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

    def test_empty_line(self):
        process, master = SpawnShellhop("abc")
        self.expect(process.stderr, SAVE_CURSOR)
        self.expect(process.stderr, HIDE_CURSOR)
        self.expect(process.stderr, RESTORE_CURSOR)
        self.expect(process.stderr, '(shellhop): abc')
        self.expect(process.stderr, CLEAR)
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

        # Hit enter.
        master.write('\r')
        self.expect(process.stderr, RESTORE_CURSOR)
        self.expect(process.stderr, CLEAR)
        self.expect(process.stderr, SHOW_CURSOR)
        self.expect(process.stdout, '0\n')
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

    def test_sigint(self):
        process, master = SpawnShellhop("abc")
        self.expect(process.stderr, SAVE_CURSOR)
        self.expect(process.stderr, HIDE_CURSOR)
        self.expect(process.stderr, RESTORE_CURSOR)
        self.expect(process.stderr, '(shellhop): abc')
        self.expect(process.stderr, CLEAR)
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

        os.kill(process.pid, signal.SIGINT)
        self.expect(process.stderr, RESTORE_CURSOR)
        self.expect(process.stderr, CLEAR)
        self.expect(process.stderr, SHOW_CURSOR)
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)
        process.wait()

    def test_bash_source(self):
        script = """\
function _shellhop {
  READLINE_POINT=$(shellhop "$READLINE_LINE");
};
bind \'"\\C-xS0":beginning-of-line\';
bind -x \'"\\C-xS1":"_shellhop"\';
bind \'"\\C-x\\C-f":"\\C-xS0\\C-xS1"\';
"""

        process, master = SpawnShellhop("-b")
        self.expect(process.stdout, script)
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

        process, master = SpawnShellhop("--bash")
        self.expect(process.stdout, script)
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

    def test_help(self):
        help_text = """\
usage: ./shellhop [OPTION]... LINE

Do an incremental search on the given line and write the index of the first
match to stdout.

  -b, --bash  output Bash shell commands to stdout
  -h, --help  display this help and exit
"""

        process, master = SpawnShellhop("-h")
        self.expect(process.stderr, help_text)
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

        process, master = SpawnShellhop("--help")
        self.expect(process.stderr, help_text)
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)
