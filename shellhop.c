/*
 * Copyright 2017 Rich Lane
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#define _POSIX_C_SOURCE 1
#include <getopt.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <termios.h>
#include <unistd.h>

static void set_raw_mode(void);

const char* bash_source =
  "function _shellhop {\n"
  "  READLINE_POINT=$(shellhop \"$READLINE_LINE\");\n"
  "};\n"
  "bind '\"\\C-xS0\":beginning-of-line';\n"
  "bind -x '\"\\C-xS1\":\"_shellhop\"';\n"
  "bind '\"\\C-x\\C-f\":\"\\C-xS0\\C-xS1\"';\n";

struct option options[] = {
  { "help", 0, NULL, 'h' },
  { "bash", 0, NULL, 'b' },
  { NULL },
};

void usage(const char* name) {
  fprintf(
      stderr,
      "usage: %s [OPTION]... LINE\n"
      "\n"
      "Do an incremental search on the given line and write the index of the first\n"
      "match to stdout.\n"
      "\n"
      "  -b, --bash  output Bash shell commands to stdout\n"
      "  -h, --help  display this help and exit\n",
      name);
}

int main(int argc, char** argv) {
  int opt;
  while ((opt = getopt_long(argc, argv, "bh", options, NULL)) != -1) {
    switch (opt) {
    case 'b':
      printf("%s", bash_source);
      return 0;
    case 'h':
      usage(argv[0]);
      return 0;
    default:
      usage(argv[0]);
      return 1;
    }
  }

  if (argc - optind <= 0) {
    usage(argv[0]);
    return 1;
  }

  const char* line = argv[optind];

  if (isatty(STDIN_FILENO)) {
    set_raw_mode();
  }

  static char buf[BUFSIZ];
  setbuf(stderr, buf);

  char needle[BUFSIZ] = "";
  int needle_len = 0;
  int result = -1;

  fprintf(stderr, "\e[s");  // Save cursor.
  fprintf(stderr, "\e[?25l");  // Hide cursor.

  while (1) {
    fprintf(stderr, "\e[u");  // Restore cursor.
    fprintf(stderr, "(shellhop): ");
    int remain = 0;
    for (int i = 0; line[i]; i++) {
      if (needle_len > 0 && !strncmp(line + i, needle, needle_len)) {
        fprintf(stderr, "\e[7m");  // Reverse video.
        remain = needle_len;
      } else if (remain > 0 && --remain == 0) {
        fprintf(stderr, "\e[0m");  // Normal.
      }
      fputc(line[i], stderr);
    }
    fprintf(stderr, "\e[J");  // Clear from cursor to end of screen.
    fflush(stderr);
    int c = getchar();
    if (c < 0) {
      return 1;
    } else if (c == '\r') {
      char* p = strstr(line, needle);
      if (p) {
        result = p - line;
      }
      break;
    } else if (c == 127 /* DEL */) {
      if (needle_len > 0) {
        needle[--needle_len] = '\0';
      }
    } else if (c == '\e') {
      break;
    } else if (needle_len + 1 < sizeof(needle)) {
      needle[needle_len++] = c;
    }
  }

  fprintf(stderr, "\e[u");  // Restore cursor.
  fprintf(stderr, "\e[J");  // Clear from cursor to end of screen.
  fprintf(stderr, "\e[?25h");  // Show cursor.
  fflush(stderr);

  if (result != -1) {
    printf("%d\n", result);
  }
  return 0;
}

static struct termios orig_termios;

static void restore_termios(void) {
  if (tcsetattr(STDIN_FILENO, TCSAFLUSH, &orig_termios) < 0) {
    perror("tcsetattr");
    abort();
  }
}

static void sigint(int signum) {
  restore_termios();
  const char cleanup[] = "\e[u\e[J\e[?25h";
  int written = 0;
  while (written < sizeof(cleanup)) {
    int c = write(STDERR_FILENO, cleanup + written, sizeof(cleanup) - 1 - written);
    if (c > 0) {
      written += c;
    } else {
      break;
    }
  }
  signal(signum, SIG_DFL);
  raise(signum);
}

static void set_raw_mode(void) {
  if (tcgetattr(STDIN_FILENO, &orig_termios) < 0) {
    perror("tcgetattr");
    abort();
  }

  struct termios raw = orig_termios;
  raw.c_iflag &= ~ICRNL;
  raw.c_lflag &= ~(ECHO | ICANON);
  if (tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw) < 0) {
    perror("tcsetattr");
    abort();
  }

  atexit(restore_termios);
  signal(SIGINT, sigint);
}
