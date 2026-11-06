import numpy as np
from ICERPython.BitPlaneCoding.Models.ContextModel import ContextModel

class BitPlaneModel:
    levelOfDecomp = 0
    bitNum = 0
    priority = 0
    subband: str
    bitPlaneMatrix: np.array
    categoryMatrix: np.array
    context: ContextModel
    _subband_multipliers = {
        "HH": 0.5,
        "HL": 1,
        "LH": 1,
        "LL": 2
    }

    def __init__(self, level: int, bitNum: int, subband: str, bitPlane: np.array, context: ContextModel, categoryMatrix=None, signMatrix=None):
        self.levelOfDecomp = level
        self.bitNum = bitNum
        self.bitPlaneMatrix = bitPlane  
        self.categoryMatrix = np.zeros(bitPlane.shape, dtype=int) if categoryMatrix is None else categoryMatrix
        self.signMatrix = np.zeros(bitPlane.shape, dtype=int) if signMatrix is None else signMatrix
        self.context = context
        self.subband = subband
        self._calculate_priority()
    
    # Given an input of a list of coordinates, return a list of categories
    def get_categories(self, coords: list[tuple[int, int]]):
        categories = []
        for coord in coords:
            categories.append(self.categoryMatrix[coord])
        return categories
    
    def update_category(self, coord: tuple[int, int], category: int):
        self.categoryMatrix[coord] = category
    
    def _calculate_priority(self):
        # Combine bit significance and the subband weight as an integer priority offset.
        self.priority = self.bitNum + self.levelOfDecomp + int(np.log2(self._subband_multipliers[self.subband]))