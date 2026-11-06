# Entropy Coding

Here I'll explain how the bits produced by the context model are turned into a compressed byte stream, and how the decoder recovers them.

## Why not Just Store the Bits?

A bit that is equally likely to be zero or one needs about one bit of storage. A long sequence that is mostly zeros is different: storing every zero individually wastes the predictability in the sequence.

The context model gives the entropy coder each bit together with an estimated probability of zero. The coder uses this estimate to choose a code. The decoder calculates the same estimate from bits it has already reconstructed, so probabilities do not need to be stored alongside the compressed data.

## What does ICER Use?

Section IV of [The ICER Progressive Wavelet Image Compressor](https://ipnpr.jpl.nasa.gov/progress_report/42-155/155J.pdf) describes an interleaved entropy coder. It combines multiple variable-length codes, each intended for a different probability range.

If zero has probability below `1/2`, the coder complements the bit and uses the complementary probability. The decoder reverses this operation using its own identical estimate. Thus, the component codes only need to handle probabilities from `1/2` to `1`.

The implementation uses the 17 bins in Table 10 on page 24:

| Bin | Upper Probability Cutoff | Component Code |
| --- | --- | --- |
| 1 | 35298 / 65536 | Uncoded |
| 2 | 37345 / 65536 | Table 10 tree |
| 3 | 40503 / 65536 | Table 10 tree |
| 4 | 43591 / 65536 | Table 10 tree |
| 5 | 47480 / 65536 | Table 10 tree |
| 6 | 50133 / 65536 | Table 10 tree |
| 7 | 53645 / 65536 | Table 10 tree |
| 8 | 55902 / 65536 | Table 10 tree |
| 9 | 57755 / 65536 | G5 |
| 10 | 58894 / 65536 | G6 |
| 11 | 60437 / 65536 | G7 |
| 12 | 62267 / 65536 | G11 |
| 13 | 63613 / 65536 | G17 |
| 14 | 64557 / 65536 | G31 |
| 15 | 65134 / 65536 | G70 |
| 16 | 65392 / 65536 | G200 |
| 17 | 65536 / 65536 | G512 |

The intervals include their lower bound and exclude their upper bound. The initial lower bound is `1/2`. Counts initialized and rescaled as described in the bit-plane documentation keep the estimated probabilities strictly between zero and one.

## How do the Component Codes Work?

The small component codes are represented as nested tuples matching the paper's decoding-tree notation. At each tuple, an output `0` selects the first child and an output `1` selects the second. A string at a leaf is the corresponding sequence of source bits.

For the Golomb code `Gm`, an input word is either `m` zeros or fewer than `m` zeros followed by a one. The all-zero word is represented by output `1`. The other words start with output `0`, followed by a truncated-binary representation of the zero-run length.

For example, `G5` maps input `00000` to output `1`, input `1` to output `000`, and input `0001` to output `0110`. The code is useful when zero is common: a run of five zeros uses only one output bit.

## Why do the Codes Need to be Interleaved?

Bits arrive in the order selected by the bit-plane encoder, but consecutive bits can belong to different probability bins. Each bin collects its own source word. A word can remain incomplete while words in other bins become complete.

The encoder therefore maintains a queue of words in the order their first source bits arrived. It emits complete words only from the front of this queue. Emitting them in completion order instead would prevent the decoder from finding the right next word.

The queue holds up to 2048 words, following the MER implementation described on page 21. When it is full, the encoder completes the front word with artificial flush bits. It chooses the shortest output codeword consistent with the real source prefix. At the end of compression, it completes and emits all remaining words the same way.

The decoder remembers the unused suffix of a source word for each bin. It also records the number of words reconstructed when that word was read. Once a suffix has aged by the encoder's buffer capacity, its remaining bits must be artificial flush bits and are discarded. The regression tests force this condition with small buffers as well as checking the standard capacity.

## How are Files Stored?

The entropy coder returns bytes and the exact number of valid output bits. Any final partial byte is padded with zeros. This project wraps that payload in its own `.icerpy` format:

1. The eight-byte signature `ICERPY1\n`.
2. A four-byte, big-endian unsigned JSON-header length.
3. An ASCII JSON header describing image and subband shapes, coefficient bit counts, encoded-plane count, minimum loss, filter parameters, LL mean, buffer size, valid payload-bit count, and payload CRC32.
4. The entropy-coded payload.

This header is specific to ICER-Python and is not a NASA bitstream specification. The implementation uses one segment and keeps separate adaptive probability counts per subband, retaining the existing project's organization. It does not implement the independent error-containment segments in Section V.

## How does Compression Stop?

The minimum-loss value excludes low-priority magnitude planes according to Section VI.A. The byte quota is checked between planes, before the entropy coder is flushed, following the stopping approach in Section VI.B. Backlogged words can therefore cause the payload to exceed the requested quota. The header adds further overhead, especially for small images.

When decompressing a complete file, a checksum mismatch or truncated payload is rejected. With `allow_partial=True`, a shortened payload can be decoded until the next complete source bit cannot be obtained. Its intact prefix is reconstructed using the same deadzone quantizer as deliberate plane omission. This is progressive reconstruction, not protection against arbitrary bit corruption or missing middle sections of a file.