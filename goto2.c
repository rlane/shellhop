#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int main(int argc, char** argv) {
  if (argc < 2) {
    fprintf(stderr, "usage: %s LINE\n", argv[0]);
    return 1;
  }
  const char* line = argv[1];

  static char buf[BUFSIZ];
  setbuf(stderr, buf);

  char needle[64] = "";
  int needle_len = 0;
  system("tput sc >&2");
  fprintf(stderr, "\e[?25l");  // Hide cursor.

  while (1) {
    system("tput ed >&2");
    system("tput rc >&2");
    fprintf(stderr, "goto2: ");
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
    } else if (needle_len + 1< sizeof(needle)) {
      needle[needle_len++] = c;
    }
  }

  system("tput ed >&2");
  system("tput rc >&2");
  fprintf(stderr, "\e[?25h");  // Show cursor.
  return 0;
}
