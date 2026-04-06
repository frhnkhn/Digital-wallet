# Makefile for C Security Module
# Compiles security.c into a shared library usable by Python via ctypes

CC      = gcc
CFLAGS  = -Wall -Wextra -O2 -fPIC -std=c99
TARGET  = libsecurity.so
SRC     = security.c
HDR     = security.h

all: $(TARGET)

$(TARGET): $(SRC) $(HDR)
	$(CC) $(CFLAGS) -shared -o $(TARGET) $(SRC)
	@echo "✅ Built $(TARGET) successfully"

clean:
	rm -f $(TARGET) *.o

.PHONY: all clean
