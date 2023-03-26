# Bit-plane Coding

Here I'll try to explain the bit-plane encoding/decoding process of the ICER algorithm.

## What is a Bit-plane?

The best way to describe a "bit-plane" is through an example.

_Explanations/Defintions for better upcoming context_:
- Binary numbers:
  - Standard numbers operate on base-10 values
    - Every 10 digits (0-9) we add another digit.
  - Binary numbers operate on base-10 values
    - Every 2 digits (0, 1) we add another digit.
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

By focusing on transmitting just the first 2 MSB values, we were able to transmit our pixel with only a 10% error! As more bits are transmitted, we end up converging to our true pixel value, but as we've demonstrated here, it's better to priortize progressive value transmissions from MSB -> LSB.

## What is a Context Model?
_WIP_

## Why do we Need Probability Estimation?
_WIP_
