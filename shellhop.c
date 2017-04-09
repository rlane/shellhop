#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <getopt.h>

const char* bash_source =
  "function _shellhop {\n"
  "  READLINE_POINT=$(shellhop \"$READLINE_LINE\");\n"
  "};\n"
  "bind '\"\\C-xS0\":beginning-of-line';\n"
  "bind -x '\"\\C-xS1\":\"_shellhop\"';\n"
  "bind '\"\\C-x\\C-f\":\"\\C-xS0\\C-xS1\"';\n";

void usage(const char* name) {
  fprintf(stderr, "usage: %s -b|LINE\n", name);
}

int main(int argc, char** argv) {
  int opt;
  while ((opt = getopt(argc, argv, "bh")) != -1) {
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

  static char buf[BUFSIZ];
  setbuf(stderr, buf);

  char needle[BUFSIZ] = "";
  int needle_len = 0;
  fprintf(stderr, "\e[s");  // Save cursor.
  fprintf(stderr, "\e[?25l");  // Hide cursor.

  while (1) {
    fprintf(stderr, "\e[u");  // Restore cursor.
    fprintf(stderr, "(shellhop): ");
    int remain = 0;
    for (int i = 0; line[i]; i++) {
      if (needle_len > 0 && !strncmp(line + i, needle, needle_len)) {
        fprintf(stderr, "\e[4;7m%c\e[0m", line[i]);  // Reverse video, underline.
        remain = needle_len - 1;
      } else if (remain > 0) {
        fprintf(stderr, "\e[7m%c\e[0m", line[i]);  // Reverse video.
        remain--;
      } else {
        fputc(line[i], stderr);
      }
    }
    fprintf(stderr, "\e[J");  // Clear from cursor to end of screen.
    fflush(stderr);
    char c = getchar();
    if (c == '\r') {
      char* p = strstr(line, needle);
      if (p) {
        printf("%d\n", (int)(p - line));
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
  return 0;
}
