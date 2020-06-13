#!/usr/bin/env python3

import click
import serial
import structlog
import sys

from binascii import hexlify
from struct import unpack

log = structlog.get_logger()


SML_START = b"\x1B\x1B\x1B\x1B"
SML_END = SML_START + b"\x1A"
SML_V1 = b"\x01\x01\x01\x01"

SML_MSGTYPE_OCTETSTR = 0
SML_MSGTYPE_BOOL = 4
SML_MSGTYPE_INTEGER = 5
SML_MSGTYPE_UNSIGNED = 6
SML_MSGTYPE_LIST = 7
SML_MSGTYPE_ANOTHER_TL = 8

def hexlify(blob):
    return ' '.join(format(x, "02x") for x in blob)

def sml_message(msg: str) -> None:
    while msg:
        _type = msg[0] >> 4
        if _type != SML_MSGTYPE_ANOTHER_TL:
            msgtype = _type
            msglen = msg[0] & 0x0F
        else:
            # in this case the previous type is valid another time and the value 
            msglen = 48
        #print(msgtype, msglen)

        print(len(msg), msgtype, msglen, end='\t')
        if msgtype != 7:
            print(hexlify(msg[:msglen]), end='\n')
        else:
            print(hexlify([msg[0]]), end='\n')

        # cut off tlv
        msg = msg[1:]
    
        if msgtype == SML_MSGTYPE_BOOL:
            #msglen -= 0
            value = bool(msg[:msglen])
            #print(f"bool({msglen})\t{value}")
            msg = msg[msglen:]
        elif msgtype == SML_MSGTYPE_OCTETSTR:
            msglen = max(msglen - 1, 0)
            if msglen != 0:
                value = "".join(msg[:msglen])
                #.decode('latin1').decode('unicode-escape').encode('latin1').decode('utf8')
                print(f"str({msglen})\t{value}")
            msg = msg[msglen:]
        elif msgtype == SML_MSGTYPE_UNSIGNED:
            msglen -= 1
            value = int.from_bytes(msg[:msglen], byteorder="big", signed=False)
            #print(f"unsigned({msglen})\t{value}")
            msg = msg[msglen:]
        elif msgtype == SML_MSGTYPE_INTEGER:
            msglen -= 1
            value = int.from_bytes(msg[:msglen], byteorder="big", signed=True)
            #print(f"signed({msglen})\t{value}")
            msg = msg[msglen:]
        elif msgtype == SML_MSGTYPE_LIST:
            pass
            #print(f"list({msglen})")
        else:
            log.msg("unhandled tlv", type=msgtype, len=msglen)
            sys.exit(1)

    print("rest", msg)
    

@click.command()
@click.argument("device", envvar="DEVICE", type=click.Path(exists=True))
def main(device):
    buf = b''
    with serial.Serial(device, 9600) as tty:
        while True:
            buf += tty.read()
            print(f"buflen={len(buf)}\r", end='')
            sys.stdout.flush()

            # SML message is encapsulated by SML_START and SML_END
            start = buf.find(SML_START)
            end = buf.find(SML_END)

            # no start, no end
            if start == -1 or end == -1:
                continue
            # end before begin, reset
            elif start == end:
                buf = b''
                continue

            print()

            # strip start and end sequence
            msg = buf[start + len(SML_START):end]

            version = msg[:4]
            if version != SML_V1:
                log.msg("Unsupported SML version", version=version)
                buf = b''
                continue
            print("version",version)

            # strip version
            msg = msg[4:]
            print(len(msg), hexlify(msg))

            print(sml_message(msg))

            buf = b''
            

if __name__ == '__main__':
    main()
