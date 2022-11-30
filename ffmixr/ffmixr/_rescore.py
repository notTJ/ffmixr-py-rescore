import pathlib
import ffmpeg
from . import ffmixr, MediaFile

class Rescore():
    def __init__(self, config):
        self.movie = MediaFile(config=config["movie"])
        self.track = MediaFile(config=config["track"])
            
    def validate(self):
        # is it a good idea to run a probe...? For validation maybe?
        movie = pathlib.Path(self.movie.path)
        track = pathlib.Path(self.track.path)
        if not movie.is_file():
            raise FileNotFoundError
        if not track.is_file():
            raise FileNotFoundError

    def rescore(self):
        ffmixr.kill_procs()
        self.validate()
        acodec = "ac3"
        audio_ext = ".ac3"
        vcodec = "mpeg4"
        video_ext = ".mp4"
    
        moviepath = pathlib.Path(self.movie.path)
        final_cut = f'{moviepath.stem}-rescore.mkv'
        # codecs not specified. seems to be ok
        
        # Set up streams with trims
        movie_stream = ffmpeg.input(self.movie.path, ss=self.movie.startstr, to=self.movie.endstr)
        video_stream = movie_stream.video
        music_stream = ffmpeg.input(self.track.path, ss=self.track.startstr, to=self.track.endstr)
        music_stream_less_volume = ffmpeg.filter_(music_stream, "volume", 0.5)
        
        # AUDIO CHANNEL SPLIT - FC Only
        channel_args=dict()
        channel_args.update({"channel_layout": "7.1(wide)"})
        channel_args.update({"channels": "FC"})
        effects_channel_stream = ffmpeg.filter_(movie_stream, "channelsplit", **channel_args) \
                                    .filter_("volume", 3.0)
        
        # amix audio tracks
        mixed_audio_stream = ffmpeg.filter_([effects_channel_stream, music_stream_less_volume], "amix")
        
        # recombine cut video + new soundtrack
        combined_output = ffmpeg.output(mixed_audio_stream, video_stream, filename=final_cut)
        combined_output.overwrite_output().run()
        
        ## TODO: 'Smooth' Volume filter?
