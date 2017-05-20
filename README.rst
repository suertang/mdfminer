mdfminer
=======================

The project's goal is to parse a "measurement data format" files (.mdf,.dat) and provide the contents in a useful manner.

Mdf is widely used in the automotive industry and ASAM related environments. 
The format specification for Version 3.3 is available for download at
<https://vector.com/downloads/mdf_specification.pdf>.
Currently (Dec 2016) Format Version 4.X is the latest but the format specification is not available to the public. 

The mdf file format consists of a tree like structure to describe the contents referring 
to the file offset of the next block.

Tree Structure of MDF File
==========================

ID Block
__HD Block
____TX Block(File comment)(optional)
____PR Block(Program Specific Data)(optional)
____DG Block(Data Group)
______Data Record(binary)
______Trigger Block(TimingInformation)(optional)
______CG Block(s)(Channel Group(s))(optional)
________CN Block(s)(Channel(s))(optional)
________TX Block(Channel Comment)(optional)
________TX Block(Unique Identifier)
________CC Block(Channel Conversion Rule)(optional)
________CD Block(Dependencies)(optional)
________CE Block(Extentions)(optional)

How MDF works
=============

The measurement data is in the Data Record of the DG Block presenting an array of records.
The record prototype is defined by the Channel Group of the DG Block. The Channel Group consists of channels (single measurements)
and basically cuts the record into chuncks defined by bit offset and bit length.
The channels itself have a Conversion Rule on how to compute a real value out of the raw data and also provide information what physical value results.

 
How mdfminer works
==================

When loading a mdf file, the tree is read but the binary data is not touched yet.
Parsing the tree is usually very fast since it only depends on the number of channels regardless on how long the measurement really is.

Getting measurements from the mdf object  with "get_records_with_timestamp()" is done by a generator function, so the memory footprint and execution time is low until the next set of values is yield.
A set of values is presented as a common python dictionary.


Usage
=====
#import the module
import mdfminer

#create an mdf object from a recorder file
m = mdfminer.mdf(fname=r"c:\Recorder1-001.mdf")

#retrieve file version
print(m.version)
3.1

#you can dump the data into an xlsx file,
#although it is not recommended practice for data analysis
mdfminer.to_xlsx_file(m,r"c:\recorder.xlsx",useabsolutetime=True)


#recommended practice for data analysis would be feeding the generator data to your own program 
for rec in m.get_records_with_timestamp(useabsolutetime=True):
    analyze_data(rec)

