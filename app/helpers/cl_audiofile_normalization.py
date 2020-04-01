
# this module is responsible for all types of audio file normalization. That means:
#  - it normalizes names of songs, albums, artist for filesystem
#  - it tags songs
#  - it normalizes names of songs for broadcasting server
#  - it normalizes bitrate of songs for broadcasting server
#  - it normalizes volume of songs for broadcasting server


import os, re, mutagen, shutil, pathlib, subprocess
from collections import namedtuple
from app.helpers.cl_filesystem_handler import Deleter

print("importing cl audiofile normalization..")

api_broadcast_test =r"Y:\ambient\testing folder"
api_broadcast_test2 =r"Y:\ambient\testing folder2"

def get_all_audio_extensions() -> list:
    """ returns audio extensions specified in file. must be called from root of the project. works both for shell and non shell, win i linux """
    audio_extensions = pathlib.Path().absolute().joinpath('app', 'helpers','audio_extensions.txt')  
    with open(audio_extensions) as f:
        ext = f.read().splitlines()
    return ext


def move_albums_with_one_track_only(root:str) -> None:
    """ moves albums with one track to separate folder """
    singletrack_albums = []
    ext = get_all_audio_extensions()
    one_only = "_ALBUMS_WITH_ONE_TRACK_"

    for artist in os.listdir(root):
        for album in os.listdir(os.path.join(root, artist)):
            tracklist = [track for track in os.listdir(os.path.join(root, artist, album)) if track.endswith(tuple(ext))]
            if len(tracklist) == 1:
                print(f"Album '{album}' on path {os.path.join(root, artist)} has only one track")
                singletrack_albums.append(album)
                for track in tracklist:
                    src_file = os.path.join(root, artist, album, track)
                    root_one_only = root + one_only
                    dst_file = os.path.join(root_one_only, artist, album, track)
                    if not os.path.exists(os.path.dirname(dst_file)):
                        os.makedirs(os.path.join(root_one_only, artist, album))
                    print(f"Moving {src_file} to {dst_file}")
                    shutil.move(src_file, dst_file)
    print(f"Totaly: {len(singletrack_albums)} with one track only")


class RegexPatternsProvider:
    """ Base class for encapsulating regex patterns to have them in one place """

    p1_song = re.compile(r"(^\d\d)(\s)([\w+\s().,:#=`&'?!\[\]]*)$")                                          # one CD leading zero (01 song name.mp3)
    p2_song = re.compile(r"(^\d)(\s)([A-Z][\w+\s().,:#=`&'?!\[\]]*)$")                                   # one CD no leading zero (1 song name.mp3)
    p3_song = re.compile(r"(^\d\s\d\d)(\s)([\w+\s().,:#=&`'?!\[\]]*)$")                                 # multiple CD (1 01 song name.mp3)
    p4_song = re.compile(r"(^\d\d\d)(\s)([\w+\s().,:#=&'?`!\[\]]*)$")                                   # multiple CD (101 song name.mp3)

    p1_album = re.compile(r"^[a-zA-zä\s!'&.,()\-]*[\d]?[\d]?[()]?$")                                    # name of album
    p2_album = re.compile(r"^(\d\d\d\d)(\s?)([a-zA-z\s!'’&.()+~,üäöáçăóéűęěščřžýáíţ0-9\-]*)$")          # 2002 name of album
    p3_album = re.compile(r"^([a-zA-z\s!'&]*)([,]\s)(\d\d\d\d)$")                                       # name of album, 2002

    p_broadcast = re.compile(r"^(\d\d)(\s[A-Z][\w\s!'’&.()+~,üäöáçăóéűęěščřžýáíţ0-9\-]*)--(\s[A-Z][\w\s!'’&.()+~,üäöáçăóéűęěščřžýáíţ0-9\-]*)--(\s[A-Z][\w\s!'’&.()+~,üäöáçăóéűęěščřžýáíţ0-9\-]*)$")           # 01 Controlled Bleeding -- The Poisoner -- Part One.mp3

    def __repr__(self):
        return "Class for encapsulating regex patterns. Used as base class for other that inherits the data. It does not contain any functions. All data are class-level"


class NameNormalizer(RegexPatternsProvider):
    """ Class for clearing out the names of songs, artists and albums, the goal is to have:
        - Clear {artist_name} in the form of plain "artist name"          => for example "Steve Roach" 
        - Clear {album_name} in the form of plain "album name"            => for example "Structures Of Silence"
        - Clear {song name} in the of "song name" with track number       => for example "01 Early Man.mp3"
    """ 

    def strip_artist_album_name_from_songname(root:str) -> None:
        """ strip out artist name and album name if they are a part of name of a song name """
        ext = get_all_audio_extensions()
        for artist_folder in os.listdir(root):
            for album_folder in os.listdir(os.path.join(root, artist_folder)):
                tracklist = [track for track in os.listdir(os.path.join(root, artist_folder, album_folder)) if track.endswith(tuple(ext))]
                if len(tracklist) > 1 and all(artist_folder in song for song in tracklist): 
                    print(f"Album {album_folder} contains artist name '{artist_folder}' as part of all audio tracks => stripping it out..")
                    for file in os.listdir(os.path.join(root, artist_folder, album_folder)):
                        if file.endswith(tuple(ext)):
                            src_file = file
                            dst_file = file.replace(artist_folder, "", 1)
                            print(f"Renaming {os.path.join(artist_folder, album_folder, src_file)} to {os.path.join(artist_folder, album_folder, dst_file)}")
                            os.rename(os.path.join(root, artist_folder, album_folder, src_file), os.path.join(root, artist_folder, album_folder, dst_file))
                if len(tracklist) > 1 and all(album_folder in song for song in tracklist):
                    print(f"Album {album_folder} contains album name '{album_folder}' as part of all audio tracks => stripping it out..")
                    for file in os.listdir(os.path.join(root, artist_folder, album_folder)):
                        if file.endswith(tuple(ext)):
                            src_file = file
                            dst_file = file.replace(album_folder, "", 1)
                            print(f"Renaming {os.path.join(artist_folder, album_folder, src_file)} to {os.path.join(artist_folder, album_folder, dst_file)}")
                            os.rename(os.path.join(root, artist_folder, album_folder, src_file), os.path.join(root, artist_folder, album_folder, dst_file))


    def strip_year_from_songname(root:str) -> None:
        """ deletes (year) and Cd and _- from song name """
        ext = get_all_audio_extensions()
        yr_parens = re.compile(r"[(]\d\d\d\d[)]")
        cd = re.compile(r"Cd\s?\d\d?")
        for path, dirs, folders in os.walk(root):
            for file in folders:
                if file.endswith(tuple(ext)):
                    if re.search(yr_parens, file) or re.search(cd, file) or "-" in file or "_" in file or "[" in file or "]" in file:
                        new_file_name = re.sub(yr_parens, "", file).strip()
                        new_file_name = re.sub(cd, "", new_file_name).strip()
                        new_file_name = new_file_name.replace("-", " ").replace("_", " ").strip()
                        new_file_name = new_file_name.replace("[", "").replace("]", "").strip()
                        src_file = os.path.join(path, file)
                        dst_file = os.path.join(path, new_file_name)                    
                        os.rename(src_file, dst_file)


    def strip_dash_underscores_from_songname(root:str) -> None:
        """ deletes _ and - from all song names """
        ext = get_all_audio_extensions()
        for path, dirs, folders in os.walk(root):
            for file in folders:
                if file.endswith(tuple(ext)) and ("-" in file or "_" in file):
                    new_file_name = file.replace("-", " ").replace("_", " ")
                    src_name = os.path.join(path, file)
                    dst_name = os.path.join(path, new_file_name)
                    print(f"Striping -_ from song name {src_name} -> {dst_name}")
                    os.rename(src_name, dst_name)

         
    def strip_whitespaces_from_songname(root:str) -> None:
        """ delete multiple spaces in song names, ale trailing space at the end as well """
        for path, dirs, files in os.walk(root):
            for file in files:
                if "  " in file or file[0] == " ":           
                    src_file = os.path.join(path, file)
                    file = re.sub(r"[\s]+", " ", file).strip()
                    dst_file = os.path.join(path, file)
                    print(f"Stripping whitespace from {src_file} --> {dst_file}")
                    os.rename(src_file, dst_file)                   
                path_file_without_ext, ext = os.path.splitext(os.path.join(path, file))
                if path_file_without_ext[-1] == " ":
                    new_file_name = path_file_without_ext.strip()+ext
                    src_file = os.path.join(path, file)
                    dst_file = os.path.join(path, new_file_name)
                    print(f"Stripping whitespace as last char {src_file} --> {dst_file}")
                    os.rename(src_file, dst_file)   


    def strip_dot_after_track_from_songname(root:str) -> None:
        """ some songs have this format: 01. songname.mp3, or 1. songname, strip the . """
        for path, dirs, files in os.walk(root):
            for file in files:
                file_name, ext = os.path.splitext(os.path.join(path, file))
                basename = os.path.basename(file_name)
                try:
                    if os.path.basename(file_name)[2] == "." or os.path.basename(file_name)[1] == ".":
                        src_file = os.path.join(path, file)
                        dst_file = os.path.join(path, file_name.replace(".","", 1)+ext)
                        print(f"Stripping dot from {file}")
                        os.rename(src_file, dst_file)
                except IndexError as e:
                    print(f"{e}, {os.path.join(path, file)} does not have song name")


    def strip_parens_around_track_from_songname(root:str) -> None:
        """ some songs have this format: (02) Secret Light At The Upper Window, strip the () """
        ext = get_all_audio_extensions()
        for path, dirs, folders in os.walk(root):
            for file in folders:
                if file.endswith(tuple(ext)):
                    if file[0] == "(" and file[3] == ")":
                        src_name = os.path.join(path, file)
                        dst_name = os.path.join(path, file.replace("(","", 1).replace(")","", 1))
                        print(f"Stripping parens arount songname {file}")
                        os.rename(src_name, dst_name)


    def strip_whatever_from_name(s:set, substrings:list) -> None:
        """ used for manual clearing for songs or albums that had no regex match - takes a list os strings that should be stripped out """
        for path in s:
            head, tail = os.path.split(path)
            for substring in substrings:
                if substring in tail:
                    new_tail = tail.replace(substring, "").strip()
                    dst = os.path.join(head, new_tail)
                    try:
                        os.rename(path, dst)
                    except Exception as e:
                        print(e)


    def split_tracknumber_from_name_in_songname(s:set) -> None:
        """ some song have this format 10songname.mp3, this will meke it 10 songname.mp3 """
        for song in s:
            head, tail = os.path.split(song)
            if tail[:2].isdigit() and (isinstance(tail[2:], str) and tail[2] != " "):
                new_tail = tail[:2] + " " + tail[2:]
                src = song
                dst = os.path.join(head, new_tail)
                print(f"Spliting tracknumber from name {tail} -> {new_tail}")
                os.rename(src, dst)            


    def strip_year_from_albumname(root:str) -> None:
        """ deletes year from album name """
        for artist in os.listdir(root):
            for album in os.listdir(os.path.join(root, artist)):
                if NameNormalizer.p2_album.match(album) or NameNormalizer.p3_album.match(album):
                    p2_match = NameNormalizer.p2_album.match(album)
                    p3_match = NameNormalizer.p3_album.match(album)
                    try:
                        album_title = p2_match.group(3)
                    except AttributeError:
                        pass
                    try:
                        album_title = p3_match.group(1)
                    except AttributeError:
                        pass
                    
                    src_name = os.path.join(root, artist, album)
                    dst_name = os.path.join(root, artist, album_title)
                    print(f"Renaming album, stripping year {album} -> {album_title}")
                    if not os.path.exists(dst_name):
                        os.rename(src_name, dst_name)
                    else:
                        print(f"Ablbum {dst_name} already exists, removing duplicates")
                        shutil.rmtree(src_name)


    def strip_apimatch_from_albumname(root:str) -> None:
        """ strip [api match 131243] from album folder """
        for artist in os.listdir(root):
            for album in os.listdir(os.path.join(root, artist)):
                if "api match" in album:
                    album_name = album.rsplit(' [api')[0]
                    src_name = os.path.join(root, artist, album)
                    dst_name = os.path.join(root, artist, album_name)
                    print(f"reaming {src_name} to {dst_name}")
                    os.rename(src_name, dst_name)


    def lowercase_artist(root:str) -> None:
        """ make artist folder lowercase """
        for artist in os.listdir(root):
            if artist != artist.lower():
                src_name = os.path.join(root, artist)
                dst_name = os.path.join(root, artist.lower())
                print(f"Lowercasing artist {src_name} to {dst_name}")
                os.rename(src_name, dst_name)


    def titlecase_artist(root:str) -> None:
        """ make artist folder titlecase """
        for artist in os.listdir(root):
            if artist != artist.title():
                src_name = os.path.join(root, artist)
                dst_name = os.path.join(root, artist.title())
                print(f"Titlecasing artist {src_name} to {dst_name}")
                os.rename(src_name, dst_name)


    def lowercase_album(root:str) -> None:
        """ make album folder lowercase """
        for artist in os.listdir(root):
            for album in os.listdir(os.path.join(root, artist)):
                if album != album.lower():
                    src_name = os.path.join(root, artist, album)
                    dst_name = os.path.join(root, artist, album.lower())
                    print(f"Lowercasing album {src_name} to {dst_name}")
                    os.rename(src_name, dst_name)


    def titlecase_album(root:str) -> None:
        """ make album folder lowercase """
        for artist in os.listdir(root):
            for album in os.listdir(os.path.join(root, artist)):
                if album != album.title():
                    src_name = os.path.join(root, artist, album)
                    dst_name = os.path.join(root, artist, album.title())
                    print(f"Titlecasing album {src_name} to {dst_name}")
                    os.rename(src_name, dst_name)


    def lowercase_song(root:str) -> None:
        """ make song name lowercase """
        for artist in os.listdir(root):
            for album in os.listdir(os.path.join(root, artist)):
                for song in os.listdir(os.path.join(root, artist, album)):
                    if song != song.lower():
                        src_name = os.path.join(root, artist, album, song)
                        dst_name = os.path.join(root, artist, album, song.lower())
                        print(f"Lowercasing {os.path.join(artist, album, song)} ==> {os.path.join(artist, album, song.lower())}")
                        os.rename(src_name, dst_name) 


    def titlecase_song(root:str) -> None:
        """ make song name titlecased """
        for artist in os.listdir(root):
            for album in os.listdir(os.path.join(root, artist)):
                for song in os.listdir(os.path.join(root, artist, album)):
                    song_name, ext = os.path.splitext(os.path.join(root, artist, album, song))
                    if song != os.path.basename(song_name.title()+ext):
                        src_name = os.path.join(root, artist, album, song)
                        dst_name = os.path.join(root, artist, album, song_name.title()+ext)
                        print(f"Titlecasing {os.path.join(artist, album, song)} ==> {os.path.join(artist, album, os.path.basename(song_name.title()+ext))}")
                        os.rename(src_name, dst_name)


    def titlecase_all(root:str) -> None:
        """ title all names of songs, artists, albums """
        NameNormalizer.titlecase_song(root)
        NameNormalizer.titlecase_album(root)
        NameNormalizer.titlecase_artist(root)


    def lowercase_all(root:str) -> None:
        """ lowercase all names of songs, artists, albums """
        NameNormalizer.lowercase_song(root)
        NameNormalizer.lowercase_album(root)
        NameNormalizer.lowercase_artist(root)


    def __repr__(self):
        return "Class for clearing out the names of songs, albums and artists. All functions are class-level functions. Class serves simply as a namespace for functions that has something to do with normalization. Do not instantiate an object to run them."


    def __call__(self, root):
        """ Calls the functions in appropriate order. It can be called either on the clas itself NameNormalizer(path) or on an object """
        NameNormalizer.strip_apimatch_from_albumname(root)
        NameNormalizer.strip_year_from_albumname(root)
        NameNormalizer.titlecase_all(root)
        NameNormalizer.strip_year_from_songname(root)
        NameNormalizer.strip_artist_album_name_from_songname(root)
        NameNormalizer.strip_whitespaces_from_songname(root)
        NameNormalizer.strip_dot_after_track_from_songname(root)
        NameNormalizer.strip_parens_around_track_from_songname(root)
        NameNormalizer.strip_whitespaces_from_songname(root)
    

class RegexMatcher(RegexPatternsProvider):
    """ Class for checking regex matches for songs and albums """

    ext = get_all_audio_extensions()

    p1_song_matches = set() 
    p2_song_matches = set() 
    p3_song_matches = set()
    p4_song_matches = set()
    no_song_matches = set()

    p1_album_matches = set()
    p2_album_matches = set()    
    p3_album_matches = set()
    no_album_matches = set()

    def __repr__(self):
        return "Class for checking regex matches for songs and albums. All functions are class-level only, to call them, no instanace need to be created. The class is just to provide namespace."

    @classmethod
    def get_all_regex_song_match(cls, root:str) -> None:
        """ Get all audio files with particular regex pattern """
        RegexMatcher.p1_song_matches.clear() 
        RegexMatcher.p2_song_matches.clear() 
        RegexMatcher.p3_song_matches.clear()
        RegexMatcher.p4_song_matches.clear()
        RegexMatcher.no_song_matches.clear()

        for artist_folder in os.listdir(os.path.join(root)):
            for album_folder in os.listdir(os.path.join(root, artist_folder)):
                for file in os.listdir(os.path.join(root, artist_folder, album_folder)):
                    if file.endswith(tuple(RegexMatcher.ext)):
                        file, ext = os.path.splitext(file)
                        if RegexMatcher.p1_song.match(file): 
                            print(f"{file+ext} -> p1_song match")
                            RegexMatcher.p1_song_matches.add(os.path.join(root, artist_folder, album_folder, file+ext)) 
                        elif RegexMatcher.p2_song.match(file): 
                            print(f"{file+ext} -> p2_song match")
                            RegexMatcher.p2_song_matches.add(os.path.join(root, artist_folder, album_folder, file+ext)) 
                        elif RegexMatcher.p3_song.match(file): 
                            print(f"{file+ext} -> p3_song match")
                            RegexMatcher.p3_song_matches.add(os.path.join(root, artist_folder, album_folder, file+ext))
                        elif RegexMatcher.p4_song.match(file): 
                            print(f"{file+ext} -> p4_song match")
                            RegexMatcher.p4_song_matches.add(os.path.join(root, artist_folder, album_folder, file+ext))
                        else: 
                            RegexMatcher.no_song_matches.add(os.path.join(root, artist_folder, album_folder, file+ext))
                            print(f"{file+ext}  :: path {os.path.join(artist_folder, album_folder)} -> no regex match")


    @classmethod
    def get_no_regex_song_match(root:str) -> None:
        """ Get audio files that did not match any regex pattern """
        RegexMatcher.no_song_matches.clear()
        for artist_folder in os.listdir(os.path.join(root)):
            for album_folder in os.listdir(os.path.join(root, artist_folder)):
                for file in os.listdir(os.path.join(root, artist_folder, album_folder)):
                    if file.endswith(tuple(RegexMatcher.ext)):
                        file, ext = os.path.splitext(file)
                        if RegexMatcher.p1_song.match(file):      continue
                        elif RegexMatcher.p2_song.match(file):    continue
                        elif RegexMatcher.p3_song.match(file):    continue
                        elif RegexMatcher.p4_song.match(file):    continue
                        else: 
                            print(f"{file+ext} :: path {os.path.join(artist_folder, album_folder)} -> no regex match")
                            RegexMatcher.no_song_matches.add(os.path.join(root, artist_folder, album_folder, file+ext))


    @classmethod
    def get_all_regex_album_match(cls, root:str) -> None:
        """ Get regex match pattern for all albums """ 
        RegexMatcher.p1_album_matches.clear()
        RegexMatcher.p2_album_matches.clear()
        RegexMatcher.p3_album_matches.clear()
        RegexMatcher.no_album_matches.clear()
        for artist in os.listdir(root):
            for album in os.listdir(os.path.join(root, artist)):
                if RegexMatcher.p1_album.match(album): 
                    print(album, f" -> p1_album match :: path {os.path.join(root, artist)}")
                    RegexMatcher.p1_album_matches.add(os.path.join(root, artist, album))
                elif RegexMatcher.p2_album.match(album): 
                    print(album, f" -> p2_album match :: path {os.path.join(root, artist)}")
                    RegexMatcher.p2_album_matches.add(os.path.join(root, artist, album))
                elif RegexMatcher.p3_album.match(album): 
                    print(album, f" -> p3_album match :: path {os.path.join(root, artist)}")
                    RegexMatcher.p3_album_matches.add(os.path.join(root, artist, album))
                else: 
                    print(album, " -> no match")
                    RegexMatcher.no_album_matches.add(os.path.join(root, artist, album))


    @classmethod
    def get_no_regex_album_match(cls, root:str) -> None:
        """ Get albums that did not match any regex pattern """
        RegexMatcher.no_album_matches.clear()
        for artist in os.listdir(root):
            for album in os.listdir(os.path.join(root, artist)):
                if RegexMatcher.p1_album.match(album):      continue
                elif RegexMatcher.p2_album.match(album):    continue
                elif RegexMatcher.p3_album.match(album):    continue
                else: 
                    print(f"{album} :: path {os.path.join(root, artist)} -> no regex match")
                    RegexMatcher.no_album_matches.add(os.path.join(root, artist, album))
    

    @staticmethod
    def count_albums_with_regex_matched_songs(s:set) -> int:
        """ Returns number of albums whose songs did match particular regex pattern.
        Used mostly with set of not matched songs to see, how many albums will be tagged """
        uni_paths = {os.path.split(song) for song in s}
        return len(uni_paths)


    @staticmethod
    def print_albums_with_regex_matched_songs(s:set) -> int:
        """ Prints the albums whose songs did match particular regex pattern. 
        Used mostly with set of not matched songs to see, which albums will not be tagged """
        uni_paths = {os.path.dirname(song) for song in s}
        for i in uni_paths: 
            print(i)


class SongTagger(RegexPatternsProvider):
    """ Class that tags songs with album, artist, song names. The names are parsed from filesystem, and so first they need to be normalized. 
    Albums with one track only are moved to seprated folder and are not tagged.
    Albums whoses songs do not match any regex pattern are moved to seprated folder and are not tagged. 
    Empty audio folders are deleted after tagging and moving happens. """
    
    ext = get_all_audio_extensions()
    singletrack_albums = set()

    @classmethod
    def tag_songs(cls, root:str) -> None:
        """ Tag songs based on regexes """

        root_untagged = root + "_UNTAGGED_"
        root_onetrack = root + "_ONE_TRACKED_ALBUMS_"

        for artist in os.listdir(root):
            for album in os.listdir(os.path.join(root, artist)):
                songs = [track for track in os.listdir(os.path.join(root, artist, album)) if track.endswith(tuple(SongTagger.ext))]
                paths = [os.path.join(root, artist, album, track) 
                        for track in os.listdir(os.path.join(root, artist, album)) if track.endswith(tuple(SongTagger.ext))]
                if len(songs) == 1: # move albums with one song only - dont tag them 
                    print(f"Album '{album}' on path {os.path.join(root, artist)} has only one track")
                    SongTagger.singletrack_albums.add(os.path.join(root, artist, album))
                    for song in songs:
                        src_file = os.path.join(root, artist, album, song)
                        dst_file = os.path.join(root_onetrack, artist, album, song)
                        if not os.path.exists(os.path.dirname(dst_file)):
                            os.makedirs(os.path.dirname(dst_file))
                        if not os.path.exists(dst_file):
                            print(f"Moving single track album file {src_file} to {dst_file}")
                            shutil.move(src_file, dst_file)
                    continue
                for song, path in zip(songs, paths):
                    song_name = song.rsplit(".", 1)[0].title()
                    # if it finds a regex match, tag it
                    if SongTagger.p1_song.match(song_name) or SongTagger.p2_song.match(song_name) \
                    or SongTagger.p3_song.match(song_name) or SongTagger.p4_song.match(song_name):  
                        p1_match = SongTagger.p1_song.match(song_name)
                        p2_match = SongTagger.p2_song.match(song_name)
                        p3_match = SongTagger.p3_song.match(song_name)
                        p4_match = SongTagger.p4_song.match(song_name)
                        try:
                            tracknumber, _, title = p1_match.groups()
                        except AttributeError:
                            pass
                        try:
                            tracknumber, _, title = p2_match.groups()
                        except AttributeError:
                            pass
                        try:
                            tracknumber, _, title = p3_match.groups()
                        except AttributeError:
                            pass
                        try:
                            tracknumber, _, title = p4_match.groups()
                        except AttributeError:
                            pass

                        try:
                            tags = mutagen.File(path, easy=True)
                        except Exception as e:
                            print(e, f"on path {path}" )

                        try:
                            tags['album'] = album.title()
                            tags['artist'] = artist.title()
                            tags['title'] = title.title()
                            tags['tracknumber'] = tracknumber
                        except Exception as e:
                            print(e, f"path {path}")

                        try:
                            tags.save()
                        except UnboundLocalError as e:
                            print(e, f"on file {path} -> NOT TAGGED PROPERLY")
                    else: 
                        # if it finds no regex match, move it to separeted folder
                        print(f"Song on path {path} doesnt match regex -> NOT TAGGED, moving..")
                        dst_file = os.path.join(root_untagged, artist, album, song)                        
                        if not os.path.exists(os.path.dirname(dst_file)):
                            os.makedirs(os.path.dirname(dst_file))
                        if not os.path.exists(dst_file):
                            print(f"Moving untagged file {path} to {dst_file}")
                            shutil.move(path, dst_file)


    def __call__(self, root:str) -> None:
        """ Tag songs, and deletes empty folders """
        SongTagger.tag_songs(root)
        Deleter.delete_folders_without_audio(root)


    def __repr__(self) -> None:
        return "Class tagging songs with artist, album, song names. The names are parsed from filesystem. Functions are class-level only, no instance is needed. Class serves as namespace."


class FolderInfo(RegexPatternsProvider):
    """ Class for getting basic info about the albums, songs etc.. """

    ext = get_all_audio_extensions()

    @classmethod    
    def count_albums(cls, root:str) -> int:
        """ return number of albums i a root dir """
        c = 0
        for artist_folder in os.listdir(root):
            for album_folder in os.listdir(os.path.join(root, artist_folder)):
                c += 1
        return c
        

    @classmethod
    def print_dir_tree(cls, root:str) -> None:
        """ prints directory tree of all files """
        for artist in os.listdir(root):
            print(artist)
            for album in os.listdir(os.path.join(root, artist)):
                print("  ", album)
                for file in os.listdir(os.path.join(root, artist, album)):
                    print("     ", file)

    @classmethod
    def print_all_artists(cls, root:str) -> None:
        """ prints all artist folder names """
        for artist in os.listdir(root):
            print(artist)


    @classmethod
    def print_all_albums(cls, root:str) -> None:
        """ prints all album folder names """
        with open("all_albums.txt", 'w') as f:
            for artist in os.listdir(root):
                for album in os.listdir(os.path.join(root, artist)):
                    print(artist, " - ", album)
                    print(artist, " - ", album, file=f)


    @classmethod
    def print_all_songs(cls, root:str) -> None:
        """ prints all song folder names """
        for path, dirs, folders in os.walk(root):
            for file in folders:
                if file.endswith(tuple(FolderInfo.ext)):
                    print(file)


    def __repr__(self) -> None:
        return "Class for getting basic information about the folder's content. All functions are class-level only. Class name serves as namespace."


class BroadcastFileNormalizer(RegexPatternsProvider):
    """" Class for handling files used in broadcasting server. It normalizes names, bitrate and volume of songs and moves them to proper folders. Empty folders are deleted afterwards. """
    
    renamed = set()
    not_renamed = set()
    not_matched = set()

    def normalize_names(root:str) -> None:
        """ Renames songs for radio server, following this pattern: 
            01 Name Of Artist -- Name Of Album -- Name Of Song.mp3
        
        The names for artist, album, song should be first normalized using NameNormalizer class! 
        All files are moved to the particular folder '2] to be bitnormed'
        """
        ext = get_all_audio_extensions()
        basedir, taildir = os.path.split(root) # tail will be swapped to '2] to be bitnormed'
        dst_taildir = '2] to be bitnormed'

        for artist in os.listdir(root):
            for album in os.listdir(os.path.join(root, artist)):
                for song in os.listdir(os.path.join(root, artist, album)):
                    src = os.path.join(root, artist, album, song)
                    if song.endswith(tuple(ext)):
                        if(BroadcastFileNormalizer.p1_song.match(song) or BroadcastFileNormalizer.p2_song.match(song) \
                            or BroadcastFileNormalizer.p3_song.match(song) or BroadcastFileNormalizer.p4_song.match(song)):
                            p1_match = BroadcastFileNormalizer.p1_song.match(song)
                            p2_match = BroadcastFileNormalizer.p2_song.match(song)
                            p3_match = BroadcastFileNormalizer.p3_song.match(song)
                            p4_match = BroadcastFileNormalizer.p4_song.match(song)
                            try:
                                tracknumber, _, title = p1_match.groups()
                            except AttributeError:
                                pass
                            try:
                                tracknumber, _, title = p2_match.groups()
                            except AttributeError:
                                pass
                            try:
                                tracknumber, _, title = p3_match.groups()
                            except AttributeError:
                                pass
                            try:
                                tracknumber, _, title = p4_match.groups()
                            except AttributeError:
                                pass
                            
                            new_title = "".join([tracknumber, " ", artist, " -- ", album, " -- ", title])
                            dst = os.path.join(basedir, dst_taildir, artist, album, new_title)
                            dst_dir, dst_file = os.path.split(dst)
                            if not os.path.exists(dst_dir):
                                os.makedirs(dst_dir)
                            if not os.path.exists(dst):
                                print(f"Renaming for broadcast and moving from {src} to {dst}")
                                shutil.move(src, dst)
                            elif os.path.exists(dst):
                                print(f"File on path {dst} already exists, removing duplicates")
                                os.remove(src)
                            BroadcastFileNormalizer.renamed.add(dst)
                        else:
                            print(f"File on path {src} does not match any pattern --> not renamed (and moved to set)")
                            BroadcastFileNormalizer.not_renamed.add(src)


    def check_names_integrity(root:str) -> None:
        """ Check if all song name match the broadcast pattern before u move them to the server """
        ext = get_all_audio_extensions()
        for path, dirs, folders in os.walk(root):
            for file in folders:
                if file.endswith(tuple(ext)):
                    filename, ext = os.path.splitext(os.path.join(path, file))
                    if BroadcastFileNormalizer.p_broadcast.match(os.path.basename(filename)):
                        continue
                    else:
                        BroadcastFileNormalizer.not_matched.add(filename)
                        print(filename, "-> not matched")


    def check_bitrate(root: str, min_bitrate: bytes) -> dict:
        """ Make a map of files having less bitrate than specified """
        audio_extensions = os.path.join(os.path.dirname(__file__), "audio_extensions.txt")
        with open(audio_extensions) as f:
            e = f.read().splitlines()
        command = "ffprobe -v error -show_entries format=bit_rate -of default=noprint_wrappers=1:nokey=1"
        d = {}
        for path, dirs, files in os.walk(root):
            for file in files:
                if file.endswith(tuple(e)):
                    file_name = os.path.join(path, file)
                    full_command = "".join(command + f' "{file_name}"')
                    out = subprocess.check_output(full_command)
                    if out < min_bitrate:
                        d[file_name] = out
        return d


    def change_bitrate(source_dir: str) -> None:
        """Change bitrate to 128k value"""
        codec = " [lame]"
        path_replacement = "3] to be transfered"
        head, tail = os.path.split(source_dir)

        for path, dirs, files in os.walk(source_dir):
            for file in files:
                filepath_source = os.path.abspath(os.path.join(path, file))
                index = filepath_source.rfind(".") #DEBUG
                filepath_norm = filepath_source[:index] + codec + filepath_source[index:] #DEBUG
                filepath_target = filepath_norm.replace(tail, path_replacement)
            if not file.endswith(".mp3"):
                filename, extension = os.path.splitext(filepath_target)
                filepath_target = filename + ".mp3"
            dir_name = os.path.dirname(filepath_target)
            if os.path.exists(filepath_target):
                print(f"file {filepath_target} already exists, skipping..")
            else:
                if not os.path.exists(dir_name): 
                    os.makedirs(dir_name)
                print(f"encoding from {filepath_source} to {filepath_target}")
                subprocess.run(f'ffmpeg -i "{filepath_source}" -metadata comment="ripped with lame @128k" -codec:a libmp3lame -b:a 128k -ar 44100 "{filepath_target}"')

    
    def __call__(self, root:str) -> None:
        """ Normalize the names and move them to proper folders. After that delete empty folders. """
        NameNormalizer.strip_apimatch_from_albumname(root)
        NameNormalizer.titlecase_all(root)
        BroadcastFileNormalizer.normalize_names(root)
        Deleter.delete_folders_without_audio(root)


    def __repr__(self) -> None:
        return "Class for handling files used in broadcasting server. It is responsible for normalization of name, bitrate and volume of each track. All functions are class-level only. Class name serves as namespace."
