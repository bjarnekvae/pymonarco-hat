TARGET = libmonarco.so
CC = /usr/bin/arm-linux-gnueabihf-gcc
CFLAGS = -march=armv7-a -mfpu=vfpv3-d16 -mfloat-abi=hard -g -fPIC -c -Wall -Wno-write-strings -fmessage-length=0 -Wno-uninitialized -Werror=uninitialized -Wno-sign-compare -Werror=strict-aliasing -Wno-maybe-uninitialized -Wno-strict-aliasing

.PHONY: default all clean

default: $(TARGET)
all: default

ifeq (,$(subst ",,$(MONARCO_PATH)))
    $(error MONARCO_PATH is not set)
endif

SRCPATH = $(MONARCO_PATH)/src
INCLUDEPATH = -I$(MONARCO_PATH)/ -I$(MONARCO_PATH)/platform/linux
OBJECTS = dprint_flags.o dprint_flags.c $(patsubst %.c, %.o, $(wildcard $(SRCPATH)/*.c))
HEADERS = $(wildcard $(SRCPATH)/*.h) $(MONARCO_PATH)/platform/linux/monarco_platform.h

%.o: %.c $(HEADERS)
	$(CC) $(CFLAGS) $(INCLUDEPATH) -c $< -o $@

.PRECIOUS: $(TARGET) $(OBJECTS)

$(TARGET): $(OBJECTS)
	$(CC) -shared -o $(TARGET) $(patsubst %.c, %.o, $(wildcard $(SRCPATH)/*.c)) dprint_flags.o

clean:
	-rm -f *.o
	-rm -f *.so
	-rm -f $(SRCPATH)/*.o
