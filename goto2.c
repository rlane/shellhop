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

  fprintf(stderr, "\e[?25l");  // Hide cursor.
  fprintf(stderr, "goto2: %s", line);
  fflush(stderr);
  char c1 = getchar();

  fprintf(stderr, "\e[G");  // Move to column 0.
  fprintf(stderr, "\e[2K");  // Clear line.
  fprintf(stderr, "goto2: ");
  for (int i = 0, k = 'a'; line[i]; i++) {
    if (line[i] == c1 && k <= 'z') {
      fprintf(stderr, "\e[7m%c\e[0m", k++);  // Reverse video.
    } else {
      fputc(line[i], stderr);
    }
  }
  fflush(stderr);

  char c2 = getchar();
  for (int i = 0, k = 'a'; line[i] && k <= 'z'; i++) {
    if (line[i] == c1 && k++ == c2) {
      printf("%d\n", i);
      break;
    }
  }

  fprintf(stderr, "\e[G");  // Move to column 0.
  fprintf(stderr, "\e[2K");  // Clear line.
  fprintf(stderr, "\e[?25h");  // Show cursor.
  return 0;
}
