# An operational IXF to JSON converter

A utility that converts IBM DB2 exported IXF to JSON format!

## Usage

The package `ixf2json` contains only one function named `convert()`. 

```python
def convert(filein, fileout, encoding='utf-8') -> bool
```

It takes three parameters.

* `filein`: The relative or absolute path and FULL name of the IXF file as input.
* `fileout`: The relative or absolute path and FULL file name of the JSON file as output.
* `encoding`: A string which specifies the encoding of CHAR and VARCHAR type. It can be omitted and the function will take `utf-8` as the default value.

## Example

```python
import ixf2json

ixf2json.convert('test.ixf', 'test.json', encoding='gbk')
```

## References

[PC/IXF record types](https://www.ibm.com/support/knowledgecenter/SSEPGG_9.7.0/com.ibm.db2.luw.admin.dm.doc/doc/r0004668.html)

[PC/IXF data types](https://www.ibm.com/support/knowledgecenter/SSEPGG_9.7.0/com.ibm.db2.luw.admin.dm.doc/doc/r0004669.html)

[Packed-Decimal Format of IBM System/370](https://www.ibm.com/support/knowledgecenter/en/ssw_ibm_i_73/rzasd/padecfo.htm)

## Thanks To

This project is inspir'd by [sapenov's IXF converter](https://github.com/sapenov/IXF). Although it's unfinish'd and not operational, I did get some inspiration from it, especially the method of reading the metadata of an IXF file.