from .astronaut import AstronautFace
from .colony import ColonyFace
from .control import ControlFace
from .cosmonaut import CosmonautFace
from .explorer import ExplorerFace
from .launch import LaunchFace
from .mandala import MandalaFace
from .orbit import OrbitFace
from .rainbow import RainbowFace
from .rings import RingsFace
from .saturn import SaturnFace
from .orrery import OrreryFace
from .pixel import PixelFace
from .spiral import SpiralFace
from .station import StationFace
from .tunnel import TunnelFace
from .vision import VisionFace

FACES = {face.name: face for face in (OrreryFace, CosmonautFace, OrbitFace, SaturnFace, PixelFace,
                                      LaunchFace, AstronautFace, ControlFace, ColonyFace, StationFace, ExplorerFace,
                                      RainbowFace, VisionFace, TunnelFace, RingsFace, MandalaFace, SpiralFace)}
