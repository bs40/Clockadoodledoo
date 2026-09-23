from .cosmonaut import CosmonautFace
from .orbit import OrbitFace
from .saturn import SaturnFace
from .orrery import OrreryFace
from .pixel import PixelFace

FACES = {face.name: face for face in (OrreryFace, CosmonautFace, OrbitFace, SaturnFace, PixelFace)}
