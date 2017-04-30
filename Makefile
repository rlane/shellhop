CFLAGS := -Wall -O2 -static -std=c99

ifeq ($(COVERAGE),1)
CFLAGS += -fprofile-arcs -ftest-coverage -DUSE_GCOV=1
LDFLAGS += -fprofile-arcs
endif

all: shellhop

check: shellhop
	python test.py

clean:
	rm -f shellhop
