#!/usr/bin/env python3
from dbus_next.aio import MessageBus
from dbus.mainloop.glib import DBusGMainLoop
import dbus
import asyncio
import os
import signal
import time
import json
import threading
from colorama import Fore, Back, Style  # Colors in terminal

DBusGMainLoop(set_as_default=True)


class Config():
    def __init__(self, path=os.path.expanduser("~/.config/autoskip"), filename="config.json"):
        self.file = os.path.join(path, filename)
        self.filename = filename
        self.path = path
        with open(self.file) as f:
            settings = json.load(f)
            self.skip_songs_under = settings['SkipSongsUnder']
            self.max_skips = settings['MaxSkips']
            self.autoskip = settings['Autoskip']
            self.refreshtime = settings['Refreshtime']

    def write(self):
        json_data = {
            'SkipSongsUnder': self.skip_songs_under,
            'MaxSkips': self.max_skips,
            'Autoskip': self.autoskip,
            'Refreshtime': 1,
            'Bluetoothskip': True
        }
        with open(self.file, "w") as f:
            json.dump(json_data, f, indent=4)


class SongConfig():
    def __init__(self, path=os.path.expanduser("~/.config/autoskip"), filename="artists.json"):
        self.file = os.path.join(path, filename)
        self.filename = filename
        self.path = path
        self.default = {
            "blacklisted": False,
            "whitelisted": False,
            "blacklisted_songs": [],
            "whitelisted_songs": []
        }
        with open(self.file) as f:
            self.artists = json.load(f)

    # Using lower level python magic this can probably be done better.
    def create(self, artist):
        if artist not in self.artists:
            self.artists[artist] = self.default
        return self.artists[artist]

    def write(self):
        # fixed_artists = {i: self.artists[i] for i in self.artists if self.artists[i] != self.default}
        with open(self.file, "w") as f:
            json.dump(self.artists, f, indent=4)


class Song():
    def __init__(self, title=None, artist=None, score=None):
        if (title and artist and score is not None):
            self.title = title
            self.artist = artist
            self.score = score
        else:
            get_info = dbus.SessionBus()
            spotify_bus = get_info.get_object("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
            spotify_properties = dbus.Interface(spotify_bus, "org.freedesktop.DBus.Properties")
            metadata = spotify_properties.Get("org.mpris.MediaPlayer2.Player", "Metadata")

            self.title = str(metadata['xesam:title'])
            self.artist = str(metadata['xesam:artist'][0])
            self.score = float(metadata['xesam:autoRating'])


def do_nothing(*args, **kwargs):
    pass


def skip():
    print(Fore.RED + 'Skipped!' + Style.RESET_ALL, end=' ')
    get_info = dbus.SessionBus()
    spotify_bus = get_info.get_object("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
    status = spotify_bus.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus', dbus_interface='org.freedesktop.DBus.Properties')
    spotify_bus.Next(dbus_interface='org.mpris.MediaPlayer2.Player', reply_handler=do_nothing, error_handler=do_nothing)


def song_print(song):
    config = Config()
    artists = SongConfig().artists

    # Needs to be '' instead of None for printing.
    scoreprefix = ''
    songprefix = ''
    artistprefix = ''
    skip_song = False

    if song.artist in artists:
        artist_config = artists[song.artist]

        # Whitelists take priority over blacklists.
        if song.title in artist_config["blacklisted_songs"]:
            songprefix = Fore.RED
            skip_song = True

        if song.title in artist_config["whitelisted_songs"]:
            songprefix = Fore.GREEN
            skip_song = False

        if artist_config["blacklisted"]:
            artistprefix = Fore.RED
            skip_song = True

        if artist_config["whitelisted"]:
            artistprefix = Fore.GREEN
            skip_song = False

        if song.score < config.skip_songs_under:
            scoreprefix = Fore.RED
            skip_song = True

    print(f'\n{scoreprefix}{song.score}{Style.RESET_ALL} {songprefix}{song.title}{Style.RESET_ALL} | {artistprefix}{song.artist}{Style.RESET_ALL} ', end='')

    if config.autoskip and skip_song:
        skip()


def toggle():
    config = Config()

    if config.autoskip:
        print(Fore.RED + 'Autoskip disabled' + Style.RESET_ALL, end=' ')
    else:
        print(Fore.GREEN + 'Autoskip enabled' + Style.RESET_ALL, end=' ')
    config.autoskip = not config.autoskip
    config.write()


def bls():
    song = Song()
    song_config = SongConfig()

    current_song = song_config.create(song.artist)
    if song.title in current_song["blacklisted_songs"]:
        current_song["blacklisted_songs"].remove(song.title)
        text = f'{Fore.RED}Removed{Style.RESET_ALL} "{song.title}" from blacklisted songs'
    else:
        current_song["blacklisted_songs"].append(song.title)
        text = f'{Fore.GREEN}Added{Style.RESET_ALL} "{song.title}" to blacklisted songs'
        skip()

    print(text, end=' ')
    song_config.write()


def bla():
    song = Song()
    song_config = SongConfig()

    current_song = song_config.create(song.artist)
    if current_song["blacklisted"]:
        text = f'{Fore.RED}Removed{Style.RESET_ALL} "{song.artist}" from blacklisted artists'
    else:
        text = f'{Fore.GREEN}Added{Style.RESET_ALL} "{song.title}" to blacklisted artists'
        skip()

    current_song["blacklisted"] = not current_song["blacklisted"]
    print(text, end=' ')
    song_config.write()


def wls():
    song = Song()
    song_config = SongConfig()

    current_song = song_config.create(song.artist)
    if song.title in current_song["whitelisted_songs"]:
        current_song["whitelisted_songs"].remove(song.title)
        text = f'{Fore.RED}Removed{Style.RESET_ALL} "{song.title}" from whitelisted songs'
    else:
        current_song["whitelisted_songs"].append(song.title)
        text = f'{Fore.GREEN}Added{Style.RESET_ALL} "{song.title}" to whitelisted songs'

    print(text, end=' ')
    song_config.write()


def wla():
    song = Song()
    song_config = SongConfig()

    current_song = song_config.create(song.artist)
    if current_song["whitelisted"]:
        text = f'{Fore.RED}Removed{Style.RESET_ALL} "{song.artist}" from whitelisted artists'
    else:
        text = f'{Fore.GREEN}Added{Style.RESET_ALL} "{song.title}" to whitelisted artists'

    current_song["whitelisted"] = not current_song["whitelisted"]
    print(text, end=' ')
    song_config.write()


def command_handler(command):
    commands = {
        't': toggle,
        'toggle': toggle,
        's': skip,
        'skip': skip,
        'bls': bls,
        'bla': bla,
        'wls': wls,
        'wla': wla,
    }
    for word in command:
        if word.lower() in commands:
            commands[word.lower()]()


class InputThread(threading.Thread):
    def signal_handler(sig, frame):
        # print('\nExiting')
        os._exit(1)

    # Ctrl + C
    signal.signal(signal.SIGINT, signal_handler)

    def run(self):
        while True:
            command = input()
            command_handler(command.split(' '))


async def main(loop):
    # Bad but necessary to prevent rerunning on the same song.
    global past_song
    config = Config()

    if config.autoskip:
        print(Fore.GREEN + 'Autoskip enabled ' + Style.RESET_ALL, end=' ')
    else:
        print(Fore.RED + 'Autoskip disabled ' + Style.RESET_ALL, end=' ')

    # Waits for spotify to connect.
    while True:
        try:
            past_song = Song()
            break
        except dbus.exceptions.DBusException:
            time.sleep(1)

    song_print(past_song)

    # Starts the input thread.
    input_thread = InputThread()
    input_thread.start()

    bus = await MessageBus().connect()
    introspection = await bus.introspect("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")

    obj = bus.get_proxy_object('org.mpris.MediaPlayer2.spotify', '/org/mpris/MediaPlayer2', introspection)
    player = obj.get_interface('org.mpris.MediaPlayer2.Player')
    properties = obj.get_interface('org.freedesktop.DBus.Properties')

    # listen to signals
    def on_properties_changed(interface_name, changed_properties, invalidated_properties):
        global past_song
        for changed, variant in changed_properties.items():
            # print(f'property changed: {changed} - {variant.value}')
            if changed == "Metadata":
                title = variant.value["xesam:title"].value
                artist = variant.value["xesam:artist"].value[0]
                score = variant.value["xesam:autoRating"].value
                song = Song(title, artist, score)
                # Comparing objects doesn't work so it compares the dict.
                # != (" ", " ", " ") to prevent skipping when spotify is used on another device and
                # metadata cannot be extrected.
                if song.__dict__ != past_song.__dict__ and (title, artist, score) != (" ", " ", " "):
                    past_song = song
                    song_print(song)

    properties.on_properties_changed(on_properties_changed)
    await loop.create_future()
    input_thread.join()


def run():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))


if __name__ == "__main__":
    run()
