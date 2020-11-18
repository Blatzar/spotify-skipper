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
from copy import deepcopy
from colorama import Fore, Back, Style, init  # Colors in terminal
from notify import notification

init(autoreset=True)
DBusGMainLoop(set_as_default=True)


def make_dir(path):
    try:
        os.makedirs(path)
    except OSError as e:
        pass


class Config():
    def __init__(self, path=None, filename="config.json"):
        self.filename = filename
        # Allows changing XDG_CONFIG_HOME
        if path is None:
            if 'XDG_CONFIG_HOME' in os.environ:
                self.path = os.path.join(os.environ.get('XDG_CONFIG_HOME'), 'autoskip')
            else:
                self.path = os.path.expanduser("~/.config/autoskip")

        self.file = os.path.join(self.path, self.filename)
        self.default = {
            "skipSongsUnder": 0.1,
            "autoSkip": True,
            "sendNotifications": True
        }

        # File generation (only first run).
        if not os.path.exists(self.file):
            make_dir(self.path)
            with open(self.file, 'w') as f:
                json.dump(self.default, f, indent=4)

        tries = 3
        for i in range(tries):
            try:
                with open(self.file) as f:
                    settings = json.load(f)
                    self.skip_songs_under = settings['skipSongsUnder']
                    self.autoskip = settings['autoSkip']
                    self.notifications = settings['sendNotifications']
                    break
            except json.decoder.JSONDecodeError as e:
                # Last try:
                if i == tries - 1:
                    raise json.decoder.JSONDecodeError("Unable to properly read config json data.", e.doc, e.pos)
                else:
                    time.sleep(1)
                    continue

    def write(self):
        json_data = {
            'skipSongsUnder': self.skip_songs_under,
            'autoSkip': self.autoskip,
            'sendNotifications': self.notifications
        }
        with open(self.file, "w") as f:
            json.dump(json_data, f, indent=4)


class SongConfig():
    def __init__(self, path=None, filename="artists.json"):
        self.filename = filename
        if path is None:
            if 'XDG_CONFIG_HOME' in os.environ:
                self.path = os.path.join(os.environ.get('XDG_CONFIG_HOME'), 'autoskip')
            else:
                self.path = os.path.expanduser("~/.config/autoskip")

        self.file = os.path.join(self.path, self.filename)
        self.default = {
            "blacklisted": False,
            "whitelisted": False,
            "blacklisted_songs": [],
            "whitelisted_songs": []
        }

        # File generation (only first run).
        if not os.path.exists(self.file):
            make_dir(self.path)
            with open(self.file, 'w') as f:
                json.dump({}, f, indent=4)

        tries = 3
        for i in range(tries):
            try:
                with open(self.file) as f:
                    self.artists = json.load(f)
                    break

            # Gets errors if it's read while it writes from another process.
            except json.decoder.JSONDecodeError as e:
                # Last try:
                if i == tries - 1:
                    raise json.decoder.JSONDecodeError("Unable to properly read artist json data.", e.doc, e.pos)
                else:
                    time.sleep(1)
                    continue

    # Using lower level python magic this can probably be done better.
    def create(self, artist):
        if artist not in self.artists:
            self.artists[artist] = deepcopy(self.default)
        return self.artists[artist]

    def write(self):
        # Cleanup defaults.
        fixed_artists = {i: self.artists[i] for i in self.artists if self.artists[i] != self.default}
        with open(self.file, "w") as f:
            json.dump(fixed_artists, f, indent=4)


class Song():
    def __init__(self, title=None, artist=None, score=None):
        if (title and artist and score is not None):
            self.title = title
            self.artist = artist
            self.score = score
        else:
            # Waits for spotify to connect.
            while True:
                try:
                    get_info = dbus.SessionBus()
                    spotify_bus = get_info.get_object("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
                    spotify_properties = dbus.Interface(spotify_bus, "org.freedesktop.DBus.Properties")
                    metadata = spotify_properties.Get("org.mpris.MediaPlayer2.Player", "Metadata")
                    break
                except dbus.exceptions.DBusException:
                    time.sleep(1)

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
        if config.notifications:
            notification('Autoskip disabled', title='Autoskipper')
    else:
        print(Fore.GREEN + 'Autoskip enabled' + Style.RESET_ALL, end=' ')
        if config.notifications:
            notification('Autoskip enabled', title='Autoskipper')
    config.autoskip = not config.autoskip
    config.write()


def notify():
    config = Config()

    if config.notifications:
        print(Fore.RED + 'Notifications disabled' + Style.RESET_ALL, end=' ')
        # notification('Notifications disabled', title='Autoskipper')
    else:
        print(Fore.GREEN + 'Notifications enabled' + Style.RESET_ALL, end=' ')
        notification('Notifications enabled', title='Autoskipper')
    config.notifications = not config.notifications
    config.write()


def bls():
    song = Song()
    song_config = SongConfig()
    current_song = song_config.create(song.artist)
    config = Config()

    if song.title in current_song["blacklisted_songs"]:
        current_song["blacklisted_songs"].remove(song.title)
        text = '{}Removed{} "' + song.title + '" from blacklisted songs'
        colored_text = text.format(Fore.RED, Style.RESET_ALL)
    else:
        current_song["blacklisted_songs"].append(song.title)
        text = '{}Added{} "' + song.title + '" to blacklisted songs'
        colored_text = text.format(Fore.GREEN, Style.RESET_ALL)
        skip()

    text = text.format('', '')
    print(colored_text, end=' ')
    if config.notifications:
        notification(text, title='Autoskipper')
    song_config.write()


def bla():
    song = Song()
    song_config = SongConfig()
    current_song = song_config.create(song.artist)
    config = Config()

    if current_song["blacklisted"]:
        text = '{}Removed{} "' + song.artist + '" from blacklisted artists'
        colored_text = text.format(Fore.RED, Style.RESET_ALL)
    else:
        text = '{}Added{} "' + song.artist + '" to blacklisted artists'
        colored_text = text.format(Fore.GREEN, Style.RESET_ALL)
        skip()

    current_song["blacklisted"] = not current_song["blacklisted"]
    text = text.format('', '')
    print(colored_text, end=' ')
    if config.notifications:
        notification(text, title='Autoskipper')
    song_config.write()


def wls():
    song = Song()
    song_config = SongConfig()
    current_song = song_config.create(song.artist)
    config = Config()

    if song.title in current_song["whitelisted_songs"]:
        current_song["whitelisted_songs"].remove(song.title)
        text = '{}Removed{} "' + song.title + '" from whitelisted songs'
        colored_text = text.format(Fore.RED, Style.RESET_ALL)
    else:
        current_song["whitelisted_songs"].append(song.title)
        text = '{}Added{} "' + song.title + '" to whitelisted songs'
        colored_text = text.format(Fore.GREEN, Style.RESET_ALL)

    text = text.format('', '')
    print(colored_text, end=' ')
    if config.notifications:
        notification(text, title='Autoskipper')
    song_config.write()


def wla():
    song = Song()
    song_config = SongConfig()
    current_song = song_config.create(song.artist)
    config = Config()

    if current_song["whitelisted"]:
        text = '{}Removed{} "' + song.artist + '" from whitelisted artists'
        colored_text = text.format(Fore.RED, Style.RESET_ALL)
    else:
        text = '{}Added{} "' + song.artist + '" to whitelisted artists'
        colored_text = text.format(Fore.GREEN, Style.RESET_ALL)

    current_song["whitelisted"] = not current_song["whitelisted"]
    text = text.format('', '')
    print(colored_text, end=' ')
    if config.notifications:
        notification(text, title='Autoskipper')
    song_config.write()


def cli_help():
    help_commands = {
        'toggle, t': 'Toggle autoskipper',
        'skip, s': 'Skip song',
        'bls': 'Toggle blacklist for current song',
        'bla': 'Toggle blacklist for current artist',
        'wls': 'Toggle whitelist for current song',
        'wla': 'Toggle whitelist for current artist',
        'notify, n': 'Toggle desktop notifications',
        'help, h': 'Show this menu'
    }
    for command, info in help_commands.items():
        print(f'{command}: {info}')


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
        'h': cli_help,
        'help': cli_help,
        'n': notify,
        'notify': notify
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

    past_song = Song()
    if (past_song.title, past_song.artist, past_song.score) != ("", "", 0):
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
                if song.__dict__ != past_song.__dict__ and (title, artist, score) != ("", "", 0):
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
