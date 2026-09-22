"""
Generate crisp PNG icons for the Chrome Extension using Python standard library.
"""
import os
import struct
import zlib

def create_png(width: int, height: int, filename: str) -> None:
    # Build image pixels (RGBA)
    # Background: vibrant indigo/blue rounded gradient with a white pulse/tracker symbol
    raw_data = bytearray()
    
    cx = width / 2.0
    cy = height / 2.0
    radius = width / 2.0
    
    for y in range(height):
        raw_data.append(0)  # PNG scanline filter byte: 0 (None)
        for x in range(width):
            dx = (x + 0.5) - cx
            dy = (y + 0.5) - cy
            dist = (dx * dx + dy * dy) ** 0.5
            
            # Rounded squircle / circular badge
            if dist <= radius:
                # Gradient from cyan/blue to indigo
                t = (x + y) / (width + height)
                r = int(37 * (1 - t) + 79 * t)
                g = int(99 * (1 - t) + 70 * t)
                b = int(235 * (1 - t) + 229 * t)
                a = 255
                
                # Antialiasing outer boundary
                if dist > radius - 1.2:
                    edge_alpha = max(0.0, min(1.0, radius - dist))
                    a = int(255 * edge_alpha)
                
                # Central activity pulse / checkmark symbol
                # Normalized coordinates -1 to 1
                nx = dx / radius
                ny = dy / radius
                
                # Draw central pulse waveform or dot
                # Point 1: (-0.5, 0), Point 2: (-0.2, 0), Point 3: (0.0, -0.4), Point 4: (0.2, 0.4), Point 5: (0.5, 0)
                is_symbol = False
                
                # Pulse line thickness
                th = 0.15 if width > 24 else 0.25
                
                if -0.6 <= nx <= -0.2:
                    if abs(ny - 0.0) <= th:
                        is_symbol = True
                elif -0.2 < nx <= 0.05:
                    # Segment from (-0.2, 0) to (0.05, -0.45)
                    expected_y = 0.0 + (ny - 0.0)
                    seg_t = (nx - (-0.2)) / 0.25
                    target_y = 0.0 * (1 - seg_t) + (-0.45) * seg_t
                    if abs(ny - target_y) <= th:
                        is_symbol = True
                elif 0.05 < nx <= 0.3:
                    # Segment from (0.05, -0.45) to (0.3, 0.4)
                    seg_t = (nx - 0.05) / 0.25
                    target_y = (-0.45) * (1 - seg_t) + (0.4) * seg_t
                    if abs(ny - target_y) <= th:
                        is_symbol = True
                elif 0.3 < nx <= 0.6:
                    if abs(ny - 0.0) <= th:
                        is_symbol = True
                
                if is_symbol:
                    r, g, b = 255, 255, 255
                
                raw_data.extend((r, g, b, a))
            else:
                # Transparent outside
                raw_data.extend((0, 0, 0, 0))

    # PNG format construction
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    compressed_data = zlib.compress(bytes(raw_data), level=9)
    
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr_data)
        + chunk(b"IDAT", compressed_data)
        + chunk(b"IEND", b"")
    )
    
    with open(filename, "wb") as f:
        f.write(png_bytes)
    print(f"Generated icon: {filename} ({width}x{height})")


def main():
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    os.makedirs(icons_dir, exist_ok=True)
    
    for size in [16, 32, 48, 128]:
        out_path = os.path.join(icons_dir, f"icon-{size}.png")
        create_png(size, size, out_path)

if __name__ == "__main__":
    main()
