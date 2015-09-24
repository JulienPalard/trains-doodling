#!/usr/bin/env python3.5


import os
import curses
import string
import random
import asyncio
import datetime


class Rail():
    def __init__(self, name, x, y):
        self.x, self.y, self.name = x, y, name
        self.lock = asyncio.Lock()
        self.train = None

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Rail {} {} {}>".format(self.x, self.y, self.name)

    def get_next(self):
        nexts = []
        if self.name == '-':
            moves = {(0, 1): ['-', '/', '\\'],
                     (-1, 1): ['/'],
                     (1, 1): ['\\']}
        if self.name == '/':
            moves = {(-1, 1): ['/', '-'],
                     (0, 1): ['-']}
        if self.name == '\\':
            moves = {(0, 1): ['-'],
                     (1, 1): ['\\', '-']}
        for direction, allowed in moves.items():
            try:
                next = self.tracks[self.y + direction[0]][
                    self.x + direction[1]]
                if next.name in allowed:
                    nexts.append(next)
            except:
                pass
        if len(nexts) == 0:
            return None
        return random.choice(nexts)


class Train():
    def __init__(self, name, rail=None, length=2):
        self.name, self.length = name, length
        self.speed = random.uniform(.01, .2)
        self.span_on = []
        self.engine_started = False
        if rail is not None:
            self.span_on.append(rail)
            for i in range(length):
                self.span_on.append(self.span_on[-1].get_next())
            # Should just fail if can't lock rails
            for rail in self.span_on:
                if rail.train is not None:
                    raise Exception("There's already a fscking train here")
            for rail in self.span_on:
                rail.train = self

    def __str__(self):
        return self.name

    async def go_forward(self):
        next_section = self.span_on[-1].get_next()
        if next_section is None:
            for rail in self.span_on:
                async with rail.lock:
                    rail.train = None
            self.engine_started = False
            return
        async with next_section.lock:
            if next_section.train is not None:
                return
            leaving = self.span_on.pop(0)
            async with leaving.lock:
                next_section.train = self
                leaving.train = None
                self.span_on.append(next_section)

    async def start(self):
        self.engine_started = True
        while self.engine_started:
            await self.go_forward()
            await asyncio.sleep(self.speed)


str_tracks = r"""
------\      /---\
       ------     \
------//     \-------\
------/               \       /-----
------------------------------
              /               \-----
-\           /
  ---       /
     \     /
      ----/
"""

str_tracks = r"""
------------------\
-------------------\
----------------\   \
-----------------\   \             /---------\
------------------\   \           /-----------\
-------------------\   \         /-------------\
--------------------\   \       /---------------\
-------------------------------------------------\
--------------------/  /  /     \-----------------\
-------------------/  /  /       \-----------------\
---------------------/  /         \-----------------\
--------------------/  /           \-----------------\
----------------------/                               \
---------------------/                                 \
                                                        \
                                                         \
                                                          \
                                                           \---------------\
                                                            \-----------\   \
                                                             \------------------
                                                              \------/

"""

tracks = [[Rail(t, x, y) for x, t in enumerate(track)]
          for y, track in
          enumerate(str_tracks.split('\n'))]

for line_of_track in tracks:
    for track in line_of_track:
        track.tracks = tracks


async def print_map(tracks):
    stdscr = curses.initscr()
    try:
        curses.noecho()
        curses.start_color()
        curses.cbreak()
        stdscr.keypad(True)
        win = curses.newwin(50, 80, 0, 0)
        for i in range(1, curses.COLORS - 1):
            print(i)
            curses.init_pair(i, i, curses.COLOR_BLACK)
        while True:
            for y, line_of_tracks in enumerate(tracks):
                for x, track in enumerate(line_of_tracks):
                    if track.train is not None:
                        if not hasattr(track.train, 'color'):
                            track.train.color = random.randint(
                                0, curses.COLORS - 1)
                        win.addch(y, x, '#',  # track.train.name,
                                  curses.color_pair(track.train.color))
                    else:
                        win.addch(y, x, track.name)
            win.refresh()
            await asyncio.sleep(.1)
    finally:
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()


async def pop_a_train(loop, track):
    async with track.lock:
        if track.train is None:
            try:
                train = Train(random.choice(string.ascii_lowercase), track, 5)
            except Exception:
                pass  # There's already a train here
            else:
                loop.call_soon(asyncio.ensure_future, train.start())


async def train_poper(loop, tracks):
    while True:
        for line in tracks:
            if len(line) > 0 and line[0].name == '-':
                if random.randint(0, 10) < 2:
                    await pop_a_train(loop, line[0])
        await asyncio.sleep(2)


loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.gather(print_map(tracks),
                                       train_poper(loop, tracks)))
