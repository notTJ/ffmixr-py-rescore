from ffmixr.ffmixr import ffmixr
from ffmixr._rescore import Rescore

# load local config and run the script as a class
config = ffmixr.load_config()
rescore = Rescore(config)          
rescore.rescore()