import fcntl
import os
import select
import subprocess
import time
import unittest

BINARY = './shellhop'


def set_nonblocking(f):
    fd = f.fileno()
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)


def SpawnShellhop(line):
    process = subprocess.Popen(
        [BINARY, line],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    set_nonblocking(process.stdout)
    set_nonblocking(process.stderr)
    return process


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
        time.sleep(timeout)
        try:
            data = f.read()
        except IOError, e:
            data = ''
        self.assertEquals(data, '')

    def test_basic(self):
        process = SpawnShellhop("abracadabra")
        self.expect(process.stderr, SAVE_CURSOR)
        self.expect(process.stderr, HIDE_CURSOR)
        self.expect(process.stderr, RESTORE_CURSOR)
        self.expect(process.stderr, '(shellhop): abracadabra')
        self.expect(process.stderr, CLEAR)
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

        # Write one character, expect two matches.
        process.stdin.write('b')
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
        process.stdin.write('ra')

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
        process.stdin.write('c')
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
        process.stdin.write('\r')
        self.expect(process.stderr, RESTORE_CURSOR)
        self.expect(process.stderr, CLEAR)
        self.expect(process.stderr, SHOW_CURSOR)
        self.expect(process.stdout, '1\n')
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

    def test_delete(self):
        process = SpawnShellhop("abc")
        self.expect(process.stderr, SAVE_CURSOR)
        self.expect(process.stderr, HIDE_CURSOR)
        self.expect(process.stderr, RESTORE_CURSOR)
        self.expect(process.stderr, '(shellhop): abc')
        self.expect(process.stderr, CLEAR)
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

        # Hit delete with no text.
        process.stdin.write('\x7f')
        self.expect(process.stderr, RESTORE_CURSOR)
        self.expect(process.stderr, '(shellhop): ')
        self.expect(process.stderr, 'abc')
        self.expect(process.stderr, CLEAR)
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

        # Write a character.
        process.stdin.write('b')
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
        process.stdin.write('\x7f')
        self.expect(process.stderr, RESTORE_CURSOR)
        self.expect(process.stderr, '(shellhop): ')
        self.expect(process.stderr, 'abc')
        self.expect(process.stderr, CLEAR)
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

    def test_empty_line(self):
        process = SpawnShellhop("abc")
        self.expect(process.stderr, SAVE_CURSOR)
        self.expect(process.stderr, HIDE_CURSOR)
        self.expect(process.stderr, RESTORE_CURSOR)
        self.expect(process.stderr, '(shellhop): abc')
        self.expect(process.stderr, CLEAR)
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

        # Hit enter.
        process.stdin.write('\r')
        self.expect(process.stderr, RESTORE_CURSOR)
        self.expect(process.stderr, CLEAR)
        self.expect(process.stderr, SHOW_CURSOR)
        self.expect(process.stdout, '0\n')
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

    def test_bash_source(self):
        script = """\
function _shellhop {
  READLINE_POINT=$(shellhop "$READLINE_LINE");
};
bind \'"\\C-xS0":beginning-of-line\';
bind -x \'"\\C-xS1":"_shellhop"\';
bind \'"\\C-x\\C-f":"\\C-xS0\\C-xS1"\';
"""

        process = SpawnShellhop("-b")
        self.expect(process.stdout, script)
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

        process = SpawnShellhop("--bash")
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

        process = SpawnShellhop("-h")
        self.expect(process.stderr, help_text)
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)

        process = SpawnShellhop("--help")
        self.expect(process.stderr, help_text)
        self.expect_nothing(process.stderr)
        self.expect_nothing(process.stdout)
