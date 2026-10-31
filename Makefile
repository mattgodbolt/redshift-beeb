# REDSHIFT - BBC Micro
#
#   make          build/redshift.ssd (+ build/redshift.json, the symbols, and
#                 build/listing.txt), and the art and room previews in
#                 build/preview
#   make run      boot it in jsbeeb, screenshot to shots/run.png
#   make check    the smoke test (tools/smoke.mjs) on MODEL (B-DFS1.2), and
#                 the level editor's checks (editor/check.mjs)
#   make ROOM=n   a test build that starts in room n (0 first), at its start
#   make disc     rebuild from a clean tree and copy the disc to redshift.ssd,
#                 which the README's play link boots
#   make ship     make disc from HEAD in a scratch worktree (so work in
#                 progress in this tree isn't on it), then commit the disc

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
# A test build's starting room (make ROOM=n); never on the shipped disc.
ROOMDEF  = $(if $(ROOM),-D START_ROOM=$(ROOM))
BUILD   := $(shell date -u '+%Y-%m-%d %H:%M') $(shell git rev-parse --short HEAD 2>/dev/null || echo NOGIT)$(shell git diff --quiet HEAD -- . ':(exclude)$(DISC)' 2>/dev/null || echo +)

.DELETE_ON_ERROR:
.PHONY: all run check disc ship clean FORCE

all: $(TARGET)

$(TARGET): $(SOURCES) $(DATA) FORCE | build
	$(ASM) -D 'BUILD="$(BUILD)"' $(ROOMDEF) -o $@ --title REDSHIFT --opt 3 --warn 2 --symbols $(@:.ssd=.json) -v -log0 build/listing.txt src/main.6502
	@grep -E '^(code|data)' build/listing.txt || true

build/data/gfx.6502: gfx/tiles.txt gfx/sprites.txt tools/mkgfx.py tools/gfxlib.py
	python3 tools/mkgfx.py $@ --preview build/preview

build/data/rooms.6502: rooms/rooms.txt gfx/tiles.txt tools/mkrooms.py tools/gfxlib.py
	python3 tools/mkrooms.py $@ --preview build/preview

build:
	mkdir -p build

run: $(TARGET)
	node tools/play.mjs 'f25,!run' shots/ --disc $(TARGET) --until game_start

check: $(TARGET)
	node tools/smoke.mjs --model $(MODEL)
	node editor/check.mjs > build/editor-check.txt || { cat build/editor-check.txt; exit 1; }

# Always from a clean tree, so the stamp names the commit the disc holds.
disc:
	@git diff --quiet HEAD -- . ':(exclude)$(DISC)' || { echo "commit first: the stamp would say +"; exit 1; }
	rm -f $(TARGET)
	$(MAKE) $(TARGET) ROOM=
	cp $(TARGET) $(DISC)

SHIP_TREE = build/ship
ship:
	rm -rf $(SHIP_TREE) && git worktree prune
	git worktree add -q --detach $(SHIP_TREE) HEAD
	$(MAKE) -C $(SHIP_TREE) disc BARON=$(abspath $(BARON))
	cp $(SHIP_TREE)/$(DISC) $(DISC)
	git worktree remove --force $(SHIP_TREE)
	git add $(DISC) && git commit -q -m "Disc: $$(git log -1 --format=%s)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"

clean:
	rm -rf build

# (The disc is always rebuilt: ROOM= changes what it is, which make can't see.)
FORCE:
