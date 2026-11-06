# Bit-plane Coding

Here I'll try to explain the bit-plane encoding/decoding process of the ICER algorithm.

## What is a Bit-plane?

The best way to describe a "bit-plane" is through an example.

_Explanations/Defintions for better upcoming context_:
- Binary numbers:
  - Standard numbers operate on base-10 values
    - Every 10 "counts" (0-9) we add another digit.
  - Binary numbers operate on base-2 values
    - Every 2 "counts" (0, 1) we add another digit.
  - Progressive counting examples between the two:
    - Base-10: 00, 01, 02, 03, 04, 05, 06, 07, 08, 09, **1**0, 11,...
    - Base-2: 00, 01, **1**0, 11, **1**00,101,...

- Most/Least Significant Bits:
  - The "Most" significant bit (MSB) of a binary number is the bit which alters the value by the largest magnitude. This will be the furthest left value in a binary value.
    - In "10" (1010), flipping the right most bit (1011) gives us "11", however, flipping the left most bit (0010) gives us "2". So the left most bit has the largest effect on our binary value.
  - The "Least" significant bit (LSB) is the exact opposite, it is the right most bit. As we saw in the previous example, flipping the right most bit changes the binary value by 1.

_Example_

Say we have a 2x2 image with pixel values of:
```
8 4
6 5
```

The binary representation of these will be:
```
1000 0100
0110 0101
```

The Nth significant bit of each pixel value forms the Nth bit-plane (MSB bit-plane consists of the the MSB of each pixel value and so on).

MSB Bit-plane being selected
```
(1)000 (0)100
(0)110 (0)101
```

MSB Bit-plane
```
1 0
0 0
```

2nd MSB Bit-plane being selected
```
1(0)00 0(1)00
0(1)10 0(1)01
```

2nd MSB Bit-plane
```
0 1
1 1
```

3rd MSB Bit-plane
```
0 0
1 0
```

LSB Bit-plane
```
0 0
0 1
```

## Why is a Bit-plane Important?

Now that you know what a bit-plane is (a collection of the values of each pixel grouped by the same Nth significant bit), we can now touch on why these are important.

ICER leans on a "progressive" encoding and transmission technique. The MSB values are prioritized in transmission as they "contain" the most amount of data about their resepective pixels. I'll prove this with a pixel magnitude value:
```
Transmitted_Value = 0
Pixel_Value = 213
Binary_Pixel_value = 11010101

# Transmit MSB
Transmitted_Binary == 10000000
Transmitted_Value == 128

# Transmit 2nd MSB
Transmitted_Binary == 11000000
Transmitted_Value == 192

# Rest of bits fail to transmit
```

$$ Error = \frac{213-192}{213} * 100 = \text{9.86 percent} $$

By focusing on transmitting just the first 2 MSB values, we were able to transmit our pixel with only a 10% error! As more bits are transmitted, we end up converging to our true pixel value, but as we've demonstrated here, it's better to prioritize progressive value transmissions from MSB -> LSB.

## What is a Context Model?
Two bits do not necessarily have the same chance of being zero. For example, a pixel surrounded by small coefficients is more likely to have another leading zero than a pixel surrounded by large coefficients. A context model groups bits with similar nearby information so that their probabilities can be estimated separately.

The important restriction is that the decoder must have the same information when it reaches each bit. This means we can only use bits that have already been encoded, not the complete original coefficient values.

ICER keeps a category for each coefficient:

- `0`: No magnitude `1` has been encoded yet.
- `1`: The first magnitude `1` and the sign have been encoded.
- `2`: One more magnitude bit has been encoded, whether it was `0` or `1`.
- `3`: At least two more magnitude bits have been encoded. Later bits use probability `1/2`.

The category matrix is shared by all magnitude planes of a subband. Each plane is visited in raster order. The encoder maintains the number of significant horizontal, vertical, and diagonal neighbors incrementally, rather than recounting every neighborhood for every bit.

Categories `0`, `1`, and `2` select contexts `0` through `11` using Tables 6 and 7 on pages 17-18 of the paper. For an HL subband, the horizontal and vertical roles are swapped. Once a coefficient becomes significant, its sign is encoded immediately. The sign prediction and sign context use Table 8, based on the already-known signs of horizontal and vertical neighbors. The bit sent to the entropy coder is the sign XOR its prediction, not the sign directly.

Unlike the eight-bit unsigned example above, wavelet coefficients can be negative and can require more than eight bits. The implementation therefore constructs planes from the absolute coefficient magnitudes, using as many planes as needed, and encodes signs separately. In the code, `bitNum = 0` denotes the least-significant magnitude plane.

## Why do we Need Probability Estimation?
The entropy coder can use fewer output bits when one value is much more likely than the other. Before encoding a bit, the context model supplies the estimated probability that this bit is zero:

$$ p_0 = \frac{\text{totalZeroBits}}{\text{totalBits}} $$

Following Section III.C on page 18 of the paper, each context starts with nominal counts of 2 zeros and 4 total bits. This gives an initial probability of `1/2` without an empty denominator. After encoding a bit, the total count increases by one, and the zero count increases only if the bit was zero.

When the total reaches 500, both counts are halved. If the zero count would become fractional, it is rounded toward a probability of `1/2`. This makes the estimate respond to recent bits instead of allowing old observations to dominate forever. Encoder and decoder update the counts in exactly the same order.

This implementation retains a separate context model for each subband. Counts and categories persist across that subband's planes, and are reset for each compression or decompression call.

## How are Bit Planes Prioritized?

Section III.A gives each subband a weight based on its decomposition level and orientation. Combining this weight with magnitude-bit significance gives an integer priority:

$$ \text{priority} = \text{bitNum} + \text{levelOfDecomp} + \log_2(\text{subband multiplier}) $$

The multipliers are `2` for LL, `1` for HL and LH, and `1/2` for HH. Higher priorities are encoded first. Ties are resolved by higher decomposition level, then LL, HL, LH, HH, as on page 15 of the paper.

For example, the least-significant level-1 HH plane has priority 0, while the least-significant level-3 LL plane has priority 4. A minimum-loss value of 2 omits all planes with priority below 2, not the same number of planes in every subband.

## How are Missing Bit Planes Reconstructed?

If the lowest `b` magnitude planes are unavailable, the quantizer step is $\Delta = 2^b$. Coefficients that have not become significant reconstruct to zero. A significant coefficient with known magnitude prefix $i\Delta$ reconstructs to magnitude $(i + 1/2)\Delta - 1$ when $b > 0$, using its decoded sign. When all planes are available, the coefficient is reconstructed exactly.

The encoder returns entropy-coded bytes together with metadata describing subband shapes, magnitude-plane counts, the number of planes encoded, and the exact number of payload bits. These let the decoder reproduce the plane order without access to the source image. See [Entropy Coding](../EntropyCoding/README.md) for the next stage.
