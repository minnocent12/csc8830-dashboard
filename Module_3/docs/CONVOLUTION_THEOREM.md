# Convolution Theorem Derivation

This typed derivation is the digitized hand-worked theory artifact for Module 3.

## Variables

- `f[x, y]`: grayscale input image intensity at pixel coordinate `(x, y)`.
- `h[m, n]`: spatial-domain blur kernel at kernel coordinate `(m, n)`.
- `g[x, y]`: filtered image.
- `*`: discrete 2D convolution.
- `F[u, v]`: 2D discrete Fourier transform (DFT) of `f[x, y]`.
- `H[u, v]`: 2D DFT of `h[m, n]`.
- `G[u, v]`: 2D DFT of `g[x, y]`.

The spatial-domain filtering operation is

```text
g[x, y] = (f * h)[x, y]
        = sum_m sum_n f[x - m, y - n] h[m, n].
```

The 2D DFT of `g` is

```text
G[u, v] = sum_x sum_y g[x, y] exp(-j 2 pi (u x / M + v y / N)).
```

Substitute the convolution definition:

```text
G[u, v] =
sum_x sum_y sum_m sum_n
f[x - m, y - n] h[m, n] exp(-j 2 pi (u x / M + v y / N)).
```

Let `a = x - m` and `b = y - n`, so `x = a + m` and `y = b + n`:

```text
G[u, v] =
sum_m sum_n h[m, n]
sum_a sum_b f[a, b]
exp(-j 2 pi (u (a + m) / M + v (b + n) / N)).
```

Split the exponential into an image-coordinate factor and a kernel-coordinate factor:

```text
G[u, v] =
sum_m sum_n h[m, n] exp(-j 2 pi (u m / M + v n / N))
sum_a sum_b f[a, b] exp(-j 2 pi (u a / M + v b / N)).
```

The second sum is the DFT of the image, `F[u, v]`. The first sum is the DFT of the kernel,
`H[u, v]`. Therefore:

```text
G[u, v] = H[u, v] F[u, v].
```

So:

```text
DFT{f * h} = DFT{f} DFT{h}
```

and the equivalent filtering result can be recovered with the inverse transform:

```text
f * h = IDFT(F[u, v] H[u, v]).
```

## Connection to the Implementation

The theorem above describes convolution on a domain where the shifted values are well-defined.
An FFT computes circular convolution unless the arrays are padded. This project zero-pads the
image by the kernel radius on all sides, embeds the kernel into the same padded shape, rolls the
kernel so its center is at the DFT origin, multiplies the spectra, applies the inverse FFT, and
crops the original image region. That recipe makes the Fourier-domain result match the
zero-boundary spatial convolution used by `cv2.filter2D`.
