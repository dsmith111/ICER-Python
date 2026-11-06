from bisect import bisect_right
from collections import deque


class EntropyCoder:
    probability_cutoffs = [35298, 37345, 40503, 43591, 47480, 50133, 53645, 55902,
                           57755, 58894, 60437, 62267, 63613, 64557, 65134, 65392, 65536]
    component_trees = [
        ("0", "1"),
        ((((("00001", "1111"), "0001"), "001"), "10"), ("01", ("110", ("00000", "1110")))),
        ((("001", (("1101", "00011"), "111")), "10"), ("01", ("0000", ("1100", "00010")))),
        (("000", "01"), ("10", ("001", "11"))),
        ((("010", ("10000", "110")), (("101", "011"), (("10001", "111"), "1001"))), "00"),
        (("00000", "1"), (("0001", "001"), ("010", ("00001", "011")))),
        ("000", (("001", "010"), ("100", ("11", ("011", "101"))))),
        ("0000", (("001", "01"), ("10", ("00010", ("00011", "11"))))),
    ]
    golomb_lengths = [5, 6, 7, 11, 17, 31, 70, 200, 512]
    _code_tables = None

    def __init__(self, buffer_size=2048):
        if not isinstance(buffer_size, int) or buffer_size < 1:
            raise ValueError("Entropy buffer size must be a positive integer")
        self.buffer_size = buffer_size
        self.code_tables = self._get_code_tables()
        self.buffer = deque()
        self.partial_words = {}
        self.output = bytearray()
        self.bit_count = 0
        self.current_byte = 0
        self.finished = False

    @classmethod
    def _get_code_tables(cls):
        if cls._code_tables is not None:
            return cls._code_tables
        tables = []
        for tree in cls.component_trees:
            words = {}
            cls._read_tree(tree, "", words)
            tables.append(words)
        for length in cls.golomb_lengths:
            words = {"0" * length: "1"}
            bit_length = (length - 1).bit_length()
            cutoff = (1 << bit_length) - length
            for zeros in range(length):
                if zeros < cutoff:
                    suffix = format(zeros, f"0{bit_length - 1}b")
                else:
                    suffix = format(zeros + cutoff, f"0{bit_length}b")
                words["0" * zeros + "1"] = "0" + suffix
            tables.append(words)

        cls._code_tables = []
        for words in tables:
            flush_words = {}
            for word, output in sorted(words.items(), key=lambda item: (len(item[1]), item[1])):
                for length in range(len(word)):
                    flush_words.setdefault(word[:length], (word, output))
            cls._code_tables.append({"encode": words, "decode": {output: word for word, output in words.items()},
                                     "flush": flush_words})
        return cls._code_tables

    @classmethod
    def _read_tree(cls, tree, prefix, words):
        if isinstance(tree, str):
            words[tree] = prefix
        else:
            cls._read_tree(tree[0], prefix + "0", words)
            cls._read_tree(tree[1], prefix + "1", words)

    @classmethod
    def get_bin(cls, probability):
        if not 0 <= probability <= 1:
            raise ValueError("Probability must be between 0 and 1")
        probability = max(probability, 1 - probability)
        return min(bisect_right(cls.probability_cutoffs, probability * 65536), 16)

    def _write_bits(self, bits):
        for bit in bits:
            self.current_byte = (self.current_byte << 1) | int(bit)
            self.bit_count += 1
            if self.bit_count % 8 == 0:
                self.output.append(self.current_byte)
                self.current_byte = 0

    def _drain_buffer(self):
        while self.buffer and self.buffer[0]["output"] is not None:
            word = self.buffer.popleft()
            self._write_bits(word["output"])

    def _flush_word(self):
        word = self.buffer[0]
        word["output"] = self.code_tables[word["bin"]]["flush"][word["word"]][1]
        del self.partial_words[word["bin"]]
        self._drain_buffer()

    def encode(self, bit, probability):
        if self.finished:
            raise ValueError("Entropy coder is already finished")
        if bit not in [0, 1]:
            raise ValueError("A bit must be 0 or 1")
        bin_index = self.get_bin(probability)
        bit = int(bit) ^ int(probability < 0.5)
        if bin_index not in self.partial_words:
            if len(self.buffer) >= self.buffer_size:
                self._flush_word()
            word = {"bin": bin_index, "word": "", "output": None}
            self.buffer.append(word)
            self.partial_words[bin_index] = word
        word = self.partial_words[bin_index]
        word["word"] += str(bit)
        word["output"] = self.code_tables[bin_index]["encode"].get(word["word"])
        if word["output"] is not None:
            del self.partial_words[bin_index]
        self._drain_buffer()

    def finish(self):
        if not self.finished:
            while self.buffer:
                self._flush_word()
            if self.bit_count % 8:
                self.output.append(self.current_byte << (8 - self.bit_count % 8))
            self.finished = True
        return bytes(self.output)


class EntropyDecoder:

    def __init__(self, encoded_bit_stream, bit_count=None, buffer_size=2048):
        self.encoded_bit_stream = encoded_bit_stream
        self.bit_count = len(encoded_bit_stream) * 8 if bit_count is None else bit_count
        if not 0 <= self.bit_count <= len(encoded_bit_stream) * 8:
            raise ValueError("Invalid encoded bit count")
        if not isinstance(buffer_size, int) or buffer_size < 1:
            raise ValueError("Entropy buffer size must be a positive integer")
        self.buffer_size = buffer_size
        self.code_tables = EntropyCoder._get_code_tables()
        self.partial_words = {}
        self.word_count = 0
        self.position = 0

    def _read_bit(self):
        if self.position >= self.bit_count:
            raise EOFError("Incomplete entropy codeword")
        bit = (self.encoded_bit_stream[self.position // 8] >> (7 - self.position % 8)) & 1
        self.position += 1
        return str(bit)

    def decode(self, probability):
        bin_index = EntropyCoder.get_bin(probability)
        if bin_index in self.partial_words:
            word, count = self.partial_words[bin_index]
            if self.word_count - count >= self.buffer_size:
                del self.partial_words[bin_index]
        if bin_index not in self.partial_words:
            output = ""
            while output not in self.code_tables[bin_index]["decode"]:
                output += self._read_bit()
            word = self.code_tables[bin_index]["decode"][output]
            self.word_count += 1
            self.partial_words[bin_index] = (word, self.word_count)
        word, count = self.partial_words[bin_index]
        bit = int(word[0]) ^ int(probability < 0.5)
        if len(word) == 1:
            del self.partial_words[bin_index]
        else:
            self.partial_words[bin_index] = (word[1:], count)
        return bit