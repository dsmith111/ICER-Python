import numpy as np
from ICERPython.BitPlaneCoding.Models import BitPlaneModel
from ICERPython.BitPlaneCoding.Models import ContextModel

# Context helpers
def determine_context(pixel_category: int, subband: str, significant_neighbors: tuple[int, int, int]):
    # h, v, d = significant_neighbors
    h = significant_neighbors["horizontal"]
    v = significant_neighbors["vertical"]
    d = significant_neighbors["diagonal"]

    if pixel_category == 0:
        if subband == "HH":
            context = context_category0_HH(h, v, d)
        elif subband == "HL":
            # In HL subband, h and v are swapped
            context = context_category0_LL_LH_HL(v, h, d)
        else:
            context = context_category0_LL_LH_HL(h, v, d)
    elif pixel_category == 1:
        context = 9 if (h == 0 and v == 0) else 10
    elif pixel_category == 2:
        context = 11
    else:
        context = None

    return context

def context_category0_LL_LH_HL(h, v, d):
    if h == 0:
        if v == 0:
            if d == 0:
                return 0
            elif d == 1:
                return 1
            else:
                return 2
        elif v == 1:
            return 3
        else:
            return 4
    elif h == 1:
        if v == 0:
            return 5
        else:
            return 7
    else:
        return 8

def context_category0_HH(h, v, d):
    total_hv = h + v
    if total_hv == 0:
        if d == 0:
            return 0
        elif d == 1:
            return 3
        else:
            return 8
    elif total_hv == 1:
        if d == 0:
            return 1
        elif d == 1:
            return 4
        elif d == 2:
            return 6
        else:
            return 8
    else:
        if d == 0:
            return 2
        elif d == 1:
            return 5
        else:
            return 7

# Bit plane helpers
# get 8 neighbors of a pixel within a numpy array
def get_neighbors(pixel_coords: tuple[int, int], array: np.array):
    x, y = pixel_coords
    neighbors = {
                 "diagonal": [],
                 "horizontal": [],
                 "vertical": [],
                 }
    for i in range(-1, 2):
        for j in range(-1, 2):
            if (i == 0 and j == 0) or x+i < 0 or y+j < 0 or x+i >= array.shape[0] or y+j >= array.shape[1]:
                continue
            if i == j:
                neighbors["diagonal"].append((x+i, y+j))
            elif i == 0:
                neighbors["horizontal"].append((x+i, y+j))
            else:
                neighbors["vertical"].append((x+i, y+j))
    return neighbors

def create_bitplane(array: np.array):
    bitplanes = {}
    for i in range(8):
        bitplanes[i] = np.zeros(array.shape, dtype=int)
    for i in range(array.shape[0]):
        for j in range(array.shape[1]):
            signed_binary = convert_to_signed_binary_helper(array[i, j])
            for k in range(8):
                bitplanes[k][i, j] = signed_binary[k]
    return bitplanes
    
    
def convert_to_signed_binary_helper(pixel_numpy: np.float64):
    pixel_int = int(pixel_numpy)
    
    if pixel_int >= 0:
        binary_value = bin(pixel_int)
    else:
        binary_value = bin(256 + pixel_int)
    
    b_index = binary_value.find('b')
    binary_value = binary_value[b_index+1:].zfill(8)
    return binary_value

# construct bit plane models from decompLevels
def construct_bit_planes(decompLevels: dict[int, dict[str, np.array]]):
    bit_plane_models = []
    for level in decompLevels:
        for subband in decompLevels[level]:
            if decompLevels[level][subband] is None:
                continue
            # Get bit plane 2d numpy array for this subband
            bit_planes = create_bitplane(decompLevels[level][subband])
            # Create context model for this subband
            context_model = ContextModel.ContextModel()
            # Create bit plane model for each bit plane
            for bitNum, bit_plane in bit_planes.items():
                if bit_plane is None:
                    continue
                
                bit_plane_models.append(BitPlaneModel.BitPlaneModel( \
                    level=level,
                    subband=subband,
                    bitNum=bitNum,
                    bitPlane=bit_plane,
                    context=context_model))
            
            # bit_plane_models.append(BitPlaneModel.BitPlaneModel(level, subband, decompLevels[level][subband]))
    return bit_plane_models