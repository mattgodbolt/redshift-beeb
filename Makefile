# REDSHIFT - BBC Micro
#
#   make          build/redshift.ssd (+ build/redshift.json, the symbols, and
#                 build/listing.txt), and the art and room previews in
#                 build/preview
#   make run      boot it in jsbeeb, screenshot to shots/run.png
#   make disc     rebuild from a clean tree and copy the disc to redshift.ssd,
#                 which the README's play link boots

BARON   ?= $(firstword $(wildcard ../baron/build/src/baron $(HOME)/dev/baron/build/src/baron) baron)
# Baron, failing on a warning too.
ASM      = BARON=$(BARON) tools/asm.sh
MODEL   ?= B-DFS1.2
export REDSHIFT_MODEL = $(MODEL)
TARGET   = build/redshift.ssd
DISC     = redshift.ssd
SOURCES  = $(wildcard src/*.6502)
DATA     = build/data/gfx.6502 build/data/rooms.6502
# Stamped into !BOOT: UTC build time and the commit, + if the tree had changes.
BUILD   := $(shell date -u '+%Y-%m-%d %H:%M') $(shell git rev-parse --short HEAD 2>/dev/null || echo NOGIT)$(shell git diff --quiet HEAD -- . ':(exclude)$(DISC)' 2>/dev/null || echo +)

.DELETE_ON_ERROR:
.PHONY: all run disc clean

all: $(TARGET)

$(TARGET): $(SOURCES) $(DATA) | build
	$(ASM) -D 'BUILD="$(BUILD)"' -o $@ --title REDSHIFT --opt 3 --warn 2 --symbols $(@:.ssd=.json) -v -log0 build/listing.txt src/main.6502
	@grep -E '^code' build/listing.txt || true

build/data/gfx.6502: gfx/tiles.txt gfx/sprites.txt tools/mkgfx.py tools/gfxlib.py
	python3 tools/mkgfx.py $@ --preview build/preview

build/data/rooms.6502: rooms/rooms.txt gfx/tiles.txt tools/mkrooms.py tools/gfxlib.py
	python3 tools/mkrooms.py $@ --preview build/preview

build:
	mkdir -p build

run: $(TARGET)
	node tools/play.mjs 'f25,!run' shots/ --disc $(TARGET) --until game_start

# Always from a clean tree, so the stamp names the commit the disc holds.
disc:
	@git diff --quiet HEAD -- . ':(exclude)$(DISC)' || { echo "commit first: the stamp would say +"; exit 1; }
	rm -f $(TARGET)
	$(MAKE) $(TARGET)
	cp $(TARGET) $(DISC)

clean:
	rm -rf build
