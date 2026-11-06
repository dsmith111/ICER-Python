import numpy as np
import json
import struct
import zlib
from ICERPython.BitPlaneCoding import helpers as bitplane_helpers
from ICERPython.BitPlaneCoding import Models as bitplane_models
from ICERPython.BitPlaneCoding.BitPlaneEncoder import BitPlaneEncoder
from ICERPython.BitPlaneCoding.BitPlaneDecoder import BitPlaneDecoder

# Progressive image compression using wavelet transform
class ICER:
    file_signature = b"ICERPY1\n"

    def __init__(self, wavelet_transform):
        self.wavelet_transform = wavelet_transform
        self.encoded_bit_stream = b""
        self.metadata = {}

    def lossless_compression(self, levels: int = 1):
        return self._compression(levels)

    def _compression(self, levels, byte_quota=None, minimum_loss=0):
        # Implement lossless compression
        # 1. Perform forward wavelet transform
        print("Performing forward wavelet transform...")
        subbands = self.wavelet_transform.forward_transform(levels)

        # 2. Create numpy array of bitplane models
        print("Constructing bitplanes...")
        low_freq_band = subbands[levels]["LL"]
        ll_mean = int(low_freq_band.sum()) // low_freq_band.size
        coding_subbands = {level: bands.copy() for level, bands in subbands.items()}
        coding_subbands[levels]["LL"] = low_freq_band - ll_mean
        bitplanes = bitplane_helpers.construct_bit_planes(coding_subbands)
        
        # 3. Encode the bitplanes (e.g., using entropy coding)
        print("Encoding bitplanes...")
        bitplane_encoder = BitPlaneEncoder(bitplanes, coding_subbands)
        payload = bitplane_encoder.encode_bit_planes(byte_quota, minimum_loss)
        self.metadata = bitplane_encoder.metadata.copy()
        self.metadata.update({"imageShape": list(self.wavelet_transform.input_image.shape), "llMean": ll_mean,
                              "filterParameters": self.wavelet_transform.filter_parameters.tolist(),
                              "payloadCRC": zlib.crc32(payload)})
        header = json.dumps(self.metadata, separators=(",", ":")).encode("ascii")
        self.encoded_bit_stream = self.file_signature + struct.pack(">I", len(header)) + header + payload
        
        print("Done encoding bitplanes.")
        return subbands

    def lossy_compression(self, bitrate=None, levels: int = 1, minimum_loss=0, byte_quota=None):
        if bitrate is not None:
            if not np.isfinite(bitrate) or bitrate <= 0:
                raise ValueError("Bitrate must be positive and finite")
            bitrate_quota = int(bitrate * self.wavelet_transform.input_image.size / 8)
            byte_quota = bitrate_quota if byte_quota is None else min(byte_quota, bitrate_quota)
        return self._compression(levels, byte_quota, minimum_loss)

    def decompression(self, encoded_bit_stream, allow_partial=False):
        prefix_length = len(self.file_signature) + 4
        if len(encoded_bit_stream) < prefix_length or not encoded_bit_stream.startswith(self.file_signature):
            raise ValueError("Not an ICER-Python compressed image")
        header_length = struct.unpack(">I", encoded_bit_stream[len(self.file_signature):prefix_length])[0]
        if header_length > 65536 or len(encoded_bit_stream) < prefix_length + header_length:
            raise ValueError("Incomplete or invalid ICER-Python header")
        try:
            metadata = json.loads(encoded_bit_stream[prefix_length:prefix_length + header_length])
            self._validate_metadata(metadata)
        except (ValueError, KeyError, TypeError, IndexError) as error:
            raise ValueError("Invalid ICER-Python header") from error
        payload = encoded_bit_stream[prefix_length + header_length:]
        expected_bytes = (metadata["bitCount"] + 7) // 8
        if len(payload) > expected_bytes or (len(payload) < expected_bytes and not allow_partial):
            raise ValueError("Incomplete or invalid ICER-Python payload")
        if len(payload) == expected_bytes and zlib.crc32(payload) != metadata["payloadCRC"]:
            raise ValueError("ICER-Python payload checksum does not match")

        decoder = BitPlaneDecoder(metadata)
        subbands = decoder.decode_bit_planes(payload, allow_partial=allow_partial)
        subbands[max(subbands)]["LL"] += metadata["llMean"]
        filter_parameters = self.wavelet_transform.filter_parameters
        self.wavelet_transform.filter_parameters = np.array(metadata["filterParameters"])
        try:
            image = self.wavelet_transform.inverse_transform(subbands)
        finally:
            self.wavelet_transform.filter_parameters = filter_parameters
        self.metadata = metadata
        self.encoded_bit_stream = encoded_bit_stream
        return image

    def _validate_metadata(self, metadata):
        height, width = metadata["imageShape"]
        if not all(isinstance(value, int) and value > 0 for value in [height, width]):
            raise ValueError("Invalid image shape")
        for name in ["bitCount", "planeCount", "minimumLoss", "bufferSize", "payloadCRC", "llMean"]:
            if not isinstance(metadata[name], int):
                raise ValueError("Invalid integer metadata")
        if min(metadata["bitCount"], metadata["planeCount"], metadata["minimumLoss"]) < 0 or metadata["bufferSize"] != 2048:
            raise ValueError("Invalid coding parameters")
        if len(metadata["filterParameters"]) != 4 or not np.all(np.isfinite(metadata["filterParameters"])):
            raise ValueError("Invalid wavelet filter parameters")
        levels = max(band[0] for band in metadata["subbands"])
        if levels > max(1, (max(height, width) - 1).bit_length()):
            raise ValueError("Invalid decomposition levels")
        expected = {}
        for level in range(1, levels + 1):
            expected[(level, "HL")] = ((height + 1) // 2, width // 2)
            expected[(level, "LH")] = (height // 2, (width + 1) // 2)
            expected[(level, "HH")] = (height // 2, width // 2)
            height, width = (height + 1) // 2, (width + 1) // 2
        expected[(levels, "LL")] = (height, width)
        actual = {}
        for level, subband, height, width, bit_count in metadata["subbands"]:
            if not all(isinstance(value, int) for value in [level, height, width, bit_count]):
                raise ValueError("Invalid subband parameters")
            if (level, subband) in actual or not 0 <= bit_count <= 62:
                raise ValueError("Invalid subband description")
            actual[(level, subband)] = (height, width)
        if actual != expected:
            raise ValueError("Subband shapes do not match image shape")
