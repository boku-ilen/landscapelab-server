from PIL import Image


def scale_epx(image: Image):
    """"Returns the image scaled up by EPX3x.
    Returns the resulting image (which is 3x the size of the original one).

    Algorithm:
    For a given (original) pixel E, the neighboring (original) pixels are fetched:
    A B C
    D E F
    G H I

    For the new (scaled) image, E is split into 9 new pixels:
    1 2 3
    4 5 6
    7 8 9

    Depending on the original neighboring pixels, these 9 new pixels are chosen.

    More information: https://en.wikipedia.org/wiki/Pixel-art_scaling_algorithms
    """

    width, height = image.size
    image_pixels = image.load()

    new_image = Image.new(image.mode, (width * 3 - 3, height * 3 - 3))
    new_image_pixels = new_image.load()

    for x in range(width - 1):
        for y in range(height - 1):
            A = image_pixels[x - 1, y - 1]
            B = image_pixels[x, y - 1]
            C = image_pixels[x + 1, y - 1]
            D = image_pixels[x - 1, y]
            E = image_pixels[x, y]
            F = image_pixels[x + 1, y]
            G = image_pixels[x - 1, y + 1]
            H = image_pixels[x, y + 1]
            I = image_pixels[x + 1, y + 1]

            new_1 = E
            new_2 = E
            new_3 = E
            new_4 = E
            new_5 = E
            new_6 = E
            new_7 = E
            new_8 = E
            new_9 = E

            if D == B and D != H and B != F: new_1 = D
            if (D == B and D != H and B != F and E != C) or (B == F and B != D and F != H and E != A): new_2 = B
            if B == F and B != D and F != H: new_3 = F
            if (H == D and H != F and D != B and E != A) or (D == B and D != H and B != F and E != G): new_4 = D
            if (B == F and B != D and F != H and E != I) or (F == H and F != B and H != D and E != C): new_6 = F
            if H == D and H != F and D != B: new_7 = D
            if (F == H and F != B and H != D and E != G) or (H == D and H != F and D != B and E != I): new_8 = H
            if F == H and F != B and H != D: new_9 = F

            new_image_pixels[x * 3, y * 3] = new_1
            new_image_pixels[x * 3 + 1, y * 3] = new_2
            new_image_pixels[x * 3 + 2, y * 3] = new_3
            new_image_pixels[x * 3, y * 3 + 1] = new_4
            new_image_pixels[x * 3 + 1, y * 3 + 1] = new_5
            new_image_pixels[x * 3 + 2, y * 3 + 1] = new_6
            new_image_pixels[x * 3, y * 3 + 2] = new_7
            new_image_pixels[x * 3 + 1, y * 3 + 2] = new_8
            new_image_pixels[x * 3 + 2, y * 3 + 2] = new_9

    return new_image
