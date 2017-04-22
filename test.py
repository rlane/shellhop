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
    stdin = os.fdopen(master, 'w', 0)
    return process, stdin, process.stdout, process.stderr


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
        process, stdin, stdout, stderr = SpawnShellhop("abracadabra")
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
        self.expect(stderr, REVERSE_VIDEO)
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
        self.expect(stderr, REVERSE_VIDEO)
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
        self.expect(stderr, REVERSE_VIDEO)
        self.expect(stderr, 'bra')
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

    def test_delete(self):
        process, stdin, stdout, stderr = SpawnShellhop("abc")
        self.expect(stderr, SAVE_CURSOR)
        self.expect(stderr, HIDE_CURSOR)
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): abc')
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        # Hit delete with no text.
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

        # Hit delete.
        stdin.write('\x7f')
        self.expect(stderr, RESTORE_CURSOR)
        self.expect(stderr, '(shellhop): ')
        self.expect(stderr, 'abc')
        self.expect(stderr, CLEAR)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

    def test_empty_line(self):
        process, stdin, stdout, stderr = SpawnShellhop("abc")
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

    def test_sigint(self):
        process, stdin, stdout, stderr = SpawnShellhop("abc")
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

        process, stdin, stdout, stderr = SpawnShellhop("-b")
        self.expect(stdout, script)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        process, stdin, stdout, stderr = SpawnShellhop("--bash")
        self.expect(stdout, script)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

    def test_help(self):
        help_text = """\
usage: ./shellhop [OPTION]... LINE

Do an incremental search on the given line and write the index of the first
match to stdout.

  -b, --bash  output Bash shell commands to stdout
  -h, --help  display this help and exit
"""

        process, stdin, stdout, stderr = SpawnShellhop("-h")
        self.expect(stderr, help_text)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)

        process, stdin, stdout, stderr = SpawnShellhop("--help")
        self.expect(stderr, help_text)
        self.expect_nothing(stderr)
        self.expect_nothing(stdout)
