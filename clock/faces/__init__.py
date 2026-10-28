from .astronaut import AstronautFace
from .colony import ColonyFace
from .control import ControlFace
from .cosmonaut import CosmonautFace
from .explorer import ExplorerFace
from .launch import LaunchFace
from .orbit import OrbitFace
from .saturn import SaturnFace
from .orrery import OrreryFace
from .pixel import PixelFace
from .station import StationFace

FACES = {face.name: face for face in (OrreryFace, CosmonautFace, OrbitFace, SaturnFace, PixelFace,
                                      LaunchFace, AstronautFace, ControlFace, ColonyFace, StationFace, ExplorerFace)}
