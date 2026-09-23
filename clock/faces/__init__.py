from .cosmonaut import CosmonautFace
from .orbit import OrbitFace
from .saturn import SaturnFace
from .orrery import OrreryFace

FACES = {face.name: face for face in (OrreryFace, CosmonautFace, OrbitFace, SaturnFace)}
