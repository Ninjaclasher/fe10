import argparse
import io
import struct


class WiiLZ77:
    TYPE_LZ77 = 0x10

    @staticmethod
    def decompress(data):
        stream = io.BytesIO(data)

        hdr = struct.unpack('<I', stream.read(4))[0]
        uncompressed_length = hdr >> 8
        compression_type = hdr & 0xff

        if compression_type != WiiLZ77.TYPE_LZ77:
            raise ValueError('Unsupported compression method %d' % compression_type)

        dout = b''

        while len(dout) < uncompressed_length:
            flags = struct.unpack('<B', stream.read(1))[0]

            for i in range(8):
                if flags & 0x80:
                    info = struct.unpack('>H', stream.read(2))[0]
                    num = 3 + ((info >> 12) & 0xf)
                    disp = info & 0xfff
                    ptr = len(dout) - (info & 0xfff) - 1
                    cnt = min(num, uncompressed_length - len(dout))
                    if ptr + cnt < len(dout):
                        dout += dout[ptr:ptr + cnt]
                    else:
                        for i in range(cnt):
                            dout += dout[ptr:ptr + 1]
                            ptr += 1
                else:
                    dout += stream.read(1)
                flags <<= 1
                if len(dout) >= uncompressed_length:
                    break

        return dout

    @staticmethod
    def compress(data):
        # We don't do any actual compression... we just need to write it in a LZ77-compatible format.
        dout = struct.pack('<I', len(data) << 8 | WiiLZ77.TYPE_LZ77)
        for i in range(0, len(data), 8):
            dout += struct.pack('<B', 0)
            dout += data[i:i + 8]
        return dout


def main():
    parser = argparse.ArgumentParser(description='Wii LZ77 Compresss/Decompress')
    parser.add_argument('action', choices=('compress', 'decompress', 'c', 'd'))
    parser.add_argument('in_file')
    parser.add_argument('out_file')
    args = parser.parse_args()

    with open(args.in_file, 'rb') as f:
        data = f.read()

    if args.action[0] == 'c':
        dout = WiiLZ77.compress(data)
    elif args.action[0] == 'd':
        dout = WiiLZ77.decompress(data)

    with open(args.out_file, 'wb') as f:
        f.write(dout)


if __name__ == '__main__':
    main()
