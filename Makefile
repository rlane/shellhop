CFLAGS := -Wall -O2 -static -std=c99
all: shellhop
check: shellhop
	python test.py
