from enum import Enum
from os import path, getcwd
import json
import pathlib
from pathlib import Path
import time
import psutil
import ffmpeg

class MediaType(Enum):
    BOTH = 0
    VIDEO = 1
    AUDIO = 2

class Codec(Enum):
    none = ""
    copy = "copy"
    
class ACodec(Enum):
    none = "none"
    flac = "flac"
    ac3 = "ac3"
    mp3 = "mp3"
    ogg = "libvorbis"
    mka = "mka"
    
class VCodec(Enum):
    none = "none"
    mp4 = "mp4"
    mkv = "mkv"

# Debug Variable ... prints command INSTEAD of execution
# TODO: Multiple debug modes. one for No-Execute and another for print along with exec
debug = True
class MediaFile():
    def __init__(self, config=None, path=None):
        if config is None and path is None: 
            raise ValueError
        if (config is not None):
            # TODO: Match against a series of valid regex expressions for time.
            # By default - demand the highest precision of time..
            # ^(2[0-3]|[01]?[0-9]):([0-5]?[0-9]):([0-5]?[0-9])$
            self.path = f".\\{config['name']}"
            self.startstr = str(config["start"])
            self.endstr = str(config["end"])
            self.start = time.strptime(self.startstr, "%H:%M:%S.%f")
            self.end = time.strptime(self.endstr, "%H:%M:%S.%f")
            # self.end_secs = time.strptime(self.movie.endstr, "%H:%M:%S.%f")
        else:
            self.path = path
            
class ffmixr():
    @staticmethod
    def kill_procs():
        # kill ffmpeg processes first.
        for proc in psutil.process_iter():
            # check whether the process name matches
            if proc.name() in ["ffmpeg.exe"]:
                proc.kill()
    
    @staticmethod
    def load_config(config_path=None):
        if config_path is None:
            # lets start with a default path, parse a default json file name, etc...
            cwd = getcwd()
            configPath = Path(path.join(cwd, 'config.json'))
            with open(configPath, 'r') as configFile:
                data=configFile.read()
            config = json.loads(data)
            return config
        
    @staticmethod
    def cut(mediafile, acodec=ACodec.none, vcodec=VCodec.none):
        # assume first video, first audio tracks.
        mediapath = pathlib.Path(mediafile.path)
        basename = mediapath.stem
        ext = pathlib.Path(mediafile.path).suffix.split('.')[1]
        # update later for other extensions...
        isvideo = ext == "mkv" 
        if not isvideo: ext = "ac3"
        inputArgs = dict(ss=mediafile.startstr, to=mediafile.endstr)
        # defults to .ac3 for audio and .mp4 for video....
        if isvideo:
            inputArgs.update(acodec=Codec.copy.value, vcodec=Codec.copy.value)
        else:
            inputArgs.update(acodec=ACodec.ac3.value)

        outpath = f".\\{basename}-cut.{ext}"
        (
            ffmpeg
            .input(mediafile.path)
            .output(outpath, **inputArgs)
            .overwrite_output()
            .run()
        )
        return MediaFile(path=outpath)

    @staticmethod
    def extract_from_container(mediafile, **kwargs):
        if not 'acodec' in kwargs and not 'vcodec'in kwargs:
            raise ValueError
        # only support extracting 1 at a time
        output_args = dict()
        path = pathlib.Path(mediafile.path)

        # no support for other containers
        if path.suffix not in [".mkv", ".mka"]:
            raise ValueError

        codec = ''
        if 'acodec' in kwargs:
            acodec = kwargs['acodec']
            acodec_arg = (Codec.copy.value, acodec.value)[acodec != ACodec.none]
            codec = (path.suffix.split('.')[1], acodec.value)[acodec != ACodec.none]
            output_args.update({'acodec': acodec_arg})

        if 'vcodec'in kwargs:
            vcodec = kwargs['vcodec']
            vcodec_arg = (Codec.copy.value, vcodec.value)[vcodec != VCodec.none]
            codec = (path.suffix.split('.')[1], vcodec.value)[vcodec != VCodec.none]
            if vcodec_arg == "mp4": vcodec_arg = "mpeg4"
            output_args.update({'vcodec': vcodec_arg})

        input = ffmpeg.input(path)
        stream = input.video if 'vcodec' in kwargs else input.audio
        outpath = ""
        if 'index' not in kwargs:
            outpath = f'.\\{path.stem}.{codec}'
        else:
            index = kwargs['index']
            splitpath = path.stem.split('-cut')
            outpath = f"{splitpath[0]}-{index}.{codec}"
        (
            ffmpeg
            .output(stream, outpath, **output_args)
            .overwrite_output()
            .run()    
        )
        return MediaFile(path=outpath)

    @staticmethod
    def split_audio(mediafile, acodec=ACodec.none):
        acodec_arg = (Codec.copy.value, acodec.value)[acodec != ACodec.none]
        channel_layout = "channel_layout=5.1(side)[FL][FR][FC][LFE][SL][SR]"
        path = pathlib.Path(mediafile.path)
        outpath = f'.\\{path.stem}-split.mka'
        kwargs = dict()
        kwargs.update({'channel_layout': channel_layout})
        output_args = dict()
        output_args.update({'map': '[FC]'})
        cmd = (
            ffmpeg
            .input(mediafile.path)
            .filter_("channelsplit", **kwargs)
            .output(outpath, acodec=acodec_arg)
            .overwrite_output()
            .run()
        )   
        return MediaFile(path=outpath)

    @staticmethod
    def extract_channel(mediafile, **kwargs):
        if 'acodec' not in kwargs: 
            raise ValueError
        acodec = kwargs['acodec']
        acodec_arg = (Codec.copy.value, acodec.value)[acodec != ACodec.none]
        path = pathlib.Path(mediafile.path)

        outpath = ""
        index = 0
        if 'index' in kwargs:
            index = kwargs['index']
            outpath = f'.\\{path.stem}-{index}.ac3'

        args = dict()
        args.update({"channel_layout": "5.1(side)"})
        args.update({"channels": "FC"})
        cmd = (
            ffmpeg
            .input(mediafile.path)
            .filter_("channelsplit", **args)
            .output(outpath, acodec=acodec_arg)
            .overwrite_output()
            # .run()
        )
        print(ffmpeg.get_args(cmd))
        cmd.run()
        return MediaFile(path=outpath)

    @staticmethod
    def amix_streams(outpath, *mediafiles, **kwargs):
        if len(mediafiles) == 0:
            raise ValueError
        inputs = [ffmpeg.input(mediafile.path).audio for mediafile in mediafiles]
        codec = "copy"

        output_args = dict
        if (mediafiles[0].path.endswith('.ac3')):
            codec = ACodec.ac3.value
        output_args.update({"acodec": codec})
        (
            ffmpeg.filter_(inputs, 'amix', inputs=len(mediafiles))
            .output(outpath, acodec=codec)
            .overwrite_output()
            .run()
        )
        return MediaFile(path=outpath)    

    @staticmethod
    def combine_inputs(outpath, mediafile_audio, mediafile_video):
        kwargs = dict({'filename': outpath, 'acodec': 'ac3', 'vcodec': 'mpeg4'})
        input_audio = ffmpeg.input(mediafile_audio.path).audio
        input_video = ffmpeg.input(mediafile_video.path).video
        (
            ffmpeg
            .output(input_audio, input_video, **kwargs)
            .run()
        )
        return MediaFile(path=outpath)