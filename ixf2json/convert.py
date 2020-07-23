import json
import logging
import os.path
from struct import unpack


def convert(filein, fileout, encoding='utf-8') -> bool:
    # Determin if input file exists
    if not os.path.exists(filein):
        logging.log(logging.ERROR, 'File does not exist!')
        return False
        
    offsets_header = {
        'IXFHRECL': 6,
        'IXFHRECT': 1,
        'IXFHID': 3,
        'IXFHVERS': 4,
        'IXFHPROD': 12,
        'IXFHDATE': 8,
        'IXFHTIME': 6,
        'IXFHHCNT': 5,
        'IXFHSBCP': 5,
        'IXFHDBCP': 5,
        'IXFHFIL1': 2
    }

    offsets_table = {
        'IXFTRECL': 6,
        'IXFTRECT': 1,
        'IXFTNAML': 3,
        'IXFTNAME': 256,
        'IXFTQULL': 3,
        'IXFTQUAL': 256,
        'IXFTSRC': 12,
        'IXFTDATA': 1,
        'IXFTFORM': 1,
        'IXFTMFRM': 5,
        'IXFTLOC': 1,
        'IXFTCCNT': 5,
        'IXFTFIL1': 2,
        'IXFTDESC': 30,
        'IXFTPKNM': 257,
        'IXFTDSPC': 257,
        'IXFTISPC': 257,
        'IXFTLSPC': 257
    }

    offsets_descriptor = {
        'IXFCRECL': 6,
        'IXFCRECT': 1,
        'IXFCNAML': 3,
        'IXFCNAME': 256,
        'IXFCNULL': 1,
        'IXFCDEF': 1,
        'IXFCSLCT': 1,
        'IXFCKPOS': 2,
        'IXFCCLAS': 1,
        'IXFCTYPE': 3,
        'IXFCSBCP': 5,
        'IXFCDBCP': 5,
        'IXFCLENG': 5,
        'IXFCDRID': 3,
        'IXFCPOSN': 6,
        'IXFCDESC': 30,
        'IXFCLOBL': 20,
        'IXFCUDTL': 3,
        'IXFCUDTN': 256,
        'IXFCDEFL': 3,
        'IXFCDEFV': 254,
        'IXFCREF': 1,
        'IXFCNDIM': 2
        # 'IXFCDSIZ' : variable   ## this att is determin'd at runtime
    }

    offsets_data = {
        'IXFDRECL': 6,
        'IXFDRECT': 1,
        'IXFDRID': 3,
        'IXFDFIL1': 4
        # 'IXFDCOLS': variable  ## this att is determin'd at runtime
    }

    fin = open(filein, 'rb')
    fout = open(fileout, 'w', encoding='utf8')

    # get header info
    header = {}
    for k, v in offsets_header.items():
        header[k] = fin.read(v)

    # get table info
    table = {}
    for k, v in offsets_table.items():
        table[k] = fin.read(v)

    # get column info
    columns = []  # Column info

    for i in range(0, int(table['IXFTCCNT'])):
        column = {}
        for k, v in offsets_descriptor.items():
            column[k] = fin.read(v)
        if column['IXFCRECT'] != b'C':
            logging.log(
                logging.INFO, 'This IXF does not contain a valid column descriptor!')
            exit()
        column['IXFCDSIZ'] = fin.read(int(column['IXFCRECL']) - 862)
        columns.append(column)

    # get data
    results = []
    endOfData = False
    # for i in range(0, 2):    ## ONLY for test use
    while(True):
        datafrag = {}
        item = {}

        for c in columns:
            pos = int(c['IXFCPOSN']) - 1
            if pos == 0:
                for k, v in offsets_data.items():
                    datafrag[k] = fin.read(v)
                datafrag['IXFDCOLS'] = fin.read(int(datafrag['IXFDRECL']) - 8)

            if (datafrag['IXFDRECT'] != b'D'):
                endOfData = True
                break

            columnName = str(c['IXFCNAME'], encoding='utf-8').strip()
            fields = datafrag['IXFDCOLS']

            # For nullable fields, IXF adds two leading bytes before the value.
            # '\xff\xff' means this field is null and you should skip it.
            # '\x00\x00' means this field is not null and you can go on to fetch the value.
            if c['IXFCNULL'] == b'Y':
                if fields[pos:pos+2] == b'\xff\xff':
                    item[columnName] = None
                    continue
                elif fields[pos:pos+2] == b'\x00\x00':
                    pos += 2

            if c['IXFCTYPE'] == b'492':  # BIGINT
                field = unpack('<q', fields[pos:pos+8])[0]
                item[columnName] = field

            elif c['IXFCTYPE'] == b'496':  # INTEGER
                field = unpack('<i', fields[pos:pos+4])[0]
                item[columnName] = field

            elif c['IXFCTYPE'] == b'452':  # CHAR
                length = int(c['IXFCLENG'])
                field = str(fields[pos:pos + length], encoding=encoding)
                item[columnName] = field

            elif c['IXFCTYPE'] == b'384':  # DATE
                field = str(fields[pos:pos+10], encoding='utf-8')
                item[columnName] = field

            elif c['IXFCTYPE'] == b'448':  # VARCHAR
                length = unpack('<h', fields[pos:pos+2])[0]
                pos += 2
                field = str(fields[pos:pos+length], encoding=encoding).strip()
                item[columnName] = field

            elif c['IXFCTYPE'] == b'484':  # DECIMAL
                p = int(c['IXFCLENG'][0:3])  # Precision
                s = int(c['IXFCLENG'][3:5])  # Scale
                length = int((p + 2) / 2)
                field = fields[pos:pos + length]

                # Process packed-decimal format as refer'd in https://www.ibm.com/support/knowledgecenter/en/ssw_ibm_i_73/rzasd/padecfo.htm
                dec = 0.0

                for b in range(0, length - 1):
                    dec = dec * 100 + int(field[b] >> 4) * \
                        10 + int(field[b] & 0x0f)
                dec = dec * 10 + int(field[-1] >> 4)

                # Detemine the positive sign
                if int(field[-1] & 0x0f) != 12:
                    dec = -dec

                item[columnName] = dec / pow(10, s)

            elif c['IXFCTYPE'] == b'392':  # TIMESTAMP
                field = str(fields[pos:pos+26], encoding='utf-8')
                item[columnName] = field

            else:
                logging.log(logging.WARNING, 'Unknown field type!')
                continue

        if endOfData:
            break

        results.append(item)

    json.dump(results, fout, ensure_ascii=False, indent=2)
    fout.close()

    return True