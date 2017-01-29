# mdf.py 
# (C) 2017 Patrick Menschel


import struct
import datetime


MDF_IMPLEMENTED_VERSION = 3.0


def get_implemented_mdf_version():
    return MDF_IMPLEMENTED_VERSION


def _interpret_id_block(data):
    """
    interprets id block of an mdf file
    @param data: the first 64 bytes of an mdf file
    @return: a dictionary with the contents
    """
    file_identifier = data[0:8].rstrip(b'\x00\x20').decode()#8byte string
    format_identifier = data[8:16].rstrip(b'\x00').decode()#8byte string
    program_string = data[16:24].rstrip(b'\x00').decode()#8byte string
    bord = struct.unpack('H',data[24:26])[0]
    if bord != 0:#byte order 0=Intel,1=Motorola
        byteorder = 'big'
        fmtprefix = '>'
    else:
        byteorder = 'little'
        fmtprefix = '<'
        
    fltfmt,vers,pnum = struct.unpack('{0}HHH'.format(fmtprefix),data[26:32])#4x uint16
    version = vers/100
    
    res1 = data[32:34]#2bytes reserved
    res2 = data[34:60]#26bytes reserved
    std_flags,cust_flags = struct.unpack('{0}HH'.format(fmtprefix),data[60:64])
    
    ret = {
            'file_identifier':file_identifier,#may be MDF (complete) or UnFinMF (incomplete)
            'format_identifier':format_identifier,#format identifier or version as string
            'program_identifier':program_string,#program that wrote this file
            'default_byte_order':byteorder,#byte order
            'default_floating-point_format':fltfmt,#float format but everything except IEEE 754 is depricated, e.g. this value must be 0
            'version_number':version,#version as float, may implement cross check later
            'code_page_number':pnum,#string encoding page defined by microsoft
            'reserved1':res1,
            'reserved2':res2,
            'standard_flags':std_flags,# some flags for file reconstruction
            'custom_flags':cust_flags,# some flags for file reconstruction
            }
    return ret


def _interpret_hd_block(data,vers=3,bord='little'):
    """
    interprets hd block of an mdf file
    @param data: the bytes of the block
    @param vers: mdf file version 
    @param bord: byte order of contents
    @note: not every block actually uses version and byte order but referred for consistency purposes
    @return: a dictionary with the contents
    """
    if bord == 'little':
        fmtprefix = '<'
    else:
        fmtprefix = '>'
    dg_ptr,fc_ptr,pb_ptr,ndg = struct.unpack("{0}IIIH".format(fmtprefix),data[4:18])
    dt = datetime.datetime.strptime(data[18:36].rstrip(b'\x00').decode(),
                                    "%d:%m:%Y%H:%M:%S")
    auths = data[36:68].rstrip(b'\x00').decode()#author
    orgs = data[68:100].rstrip(b'\x00').decode()#organisation
    subjs = data[100:132].rstrip(b'\x00').decode()#subject, e.g. vehicle information
    
    ret =  {"data_group_pointer":dg_ptr,
            "comment_text_pointer":fc_ptr,
            "program_block_pointer":pb_ptr,
            "number_of_data_groups":ndg,
            "author":auths,
            "organisation":orgs,
            "subject":subjs,
            "timestamp":dt,
            }
    return ret


def _interpret_tx_block(data,vers=3,bord='little'):
    """
    interprets tx block of an mdf file
    @param data: the bytes of the block
    @param vers: mdf file version 
    @param bord: byte order of contents
    @note: not every block actually uses version and byte order but referred for consistency purposes
    @return: a dictionary with the contents
    """
    for fmt in ["ascii","latin1"]:#ascii is standard, got a problem with german Umlaute
        try:
            text = data[4:].strip(b"\x00\x20").decode(fmt)
            break
        except UnicodeError:
            text = None
    return {"text":text}


def _interpret_pr_block(data,vers=3,bord='little'):
    """
    interprets pr block of an mdf file
    @param data: the bytes of the block
    @param vers: mdf file version 
    @param bord: byte order of contents
    @note: does only return the data contents as a dictionary for now
    @return: a dictionary with the contents
    """
    return {"data":data[4:]}


def _interpret_tr_block(data,vers=3,bord='little'):
    """
    interprets tr block of an mdf file
    @param data: the bytes of the block
    @param vers: mdf file version 
    @param bord: byte order of contents
    @note: not every block actually uses version and byte order but referred for consistency purposes
    @return: a dictionary with the contents
    """    
    if bord == 'little':
        fmtprefix = '<'
    else:
        fmtprefix = '>'
    tc_ptr,num_tevs = struct.unpack("{0}IH".format(fmtprefix),data[4:10])#trigger comment pointer,number of trigger events
    tev_lst = []
    for tev in num_tevs:
        tt,prett,posttt = struct.unpack("{0}ddd".format(fmtprefix),data[10+tev:24+tev])
        tev_lst.append({"trigger_time":tt,
                        "pre_trigger_time":prett,
                        "post_trigger_time":posttt})#trigger time, pre trigger time, post trigger time
        
    ret =  {"comment_text_pointer":tc_ptr,
            "number_of_trigger_events":num_tevs,
            "trigger_events":tev_lst,}
    return ret


def _interpret_sr_block(data,vers=3,bord='little'):
    """
    interprets sr block of an mdf file
    @param data: the bytes of the block
    @param vers: mdf file version 
    @param bord: byte order of contents
    @note: not every block actually uses version and byte order but referred for consistency purposes
    @return: a dictionary with the contents
    """
    if bord == 'little':
        fmtprefix = '<'
    else:
        fmtprefix = '>'
    nsrb_ptr,db_ptr,num_rs,loti = struct.unpack("{0}IIId".format(fmtprefix),data[4:24])#next sample reduction block pointer, data block pointer, number of reduced samples in data block, length of time interval
    ret = {"next_sample_reduction_block_pointer":nsrb_ptr,
           "data_block_pointer":db_ptr,
           "number_of_reduced_samples":num_rs,
           "length_of_time_interval":loti,}
    return ret


def _interpret_dg_block(data,vers=3,bord='little'):
    """
    interprets dg block of an mdf file
    @param data: the bytes of the block
    @param vers: mdf file version 
    @param bord: byte order of contents
    @note: not every block actually uses version and byte order but referred for consistency purposes
    @return: a dictionary with the contents
    """
    if bord == 'little':
        fmtprefix = '<'
    else:
        fmtprefix = '>'
    ndg_ptr,fcgb_ptr,tb_ptr,db_ptr,num_cg,num_rid,res = struct.unpack("{0}IIIIHHI".format(fmtprefix),data[4:28])
    ret = {"next_data_group_pointer":ndg_ptr,
           "first_channel_group_pointer":fcgb_ptr,
           "trigger_block_pointer":tb_ptr,
           "data_block_pointer":db_ptr,
           "number_of_channel_groups":num_cg,
           "number_of_record_ids":num_rid,
           "reserved":res,}
    return ret

    
def _interpret_cg_block(data,vers=3,bord='little'):
    """
    interprets cg block of an mdf file
    @param data: the bytes of the block
    @param vers: mdf file version 
    @param bord: byte order of contents
    @note: not every block actually uses version and byte order but referred for consistency purposes
    @return: a dictionary with the contents
    """    
    if bord == 'little':
        fmtprefix = '<'
    else:
        fmtprefix = '>'
    ncgb_ptr,fcb_ptr,ct_ptr = struct.unpack("{0}III".format(fmtprefix),data[4:16])
    rid,num_ch,rec_size = struct.unpack("{0}HHH".format(fmtprefix),data[16:22])
    num_recs = struct.unpack("{0}I".format(fmtprefix),data[22:26])[0]
    ret = {"next_channel_group_pointer":ncgb_ptr,
           "first_channel_pointer":fcb_ptr,
           "comment_text_pointer":ct_ptr,
           "record_id":rid,
           "number_of_channels":num_ch,
           "record_size":rec_size,
           "number_of_records":num_recs,
           }
    return ret


def _interpret_cn_block(data,vers=3.0,bord='little'):
    """
    interprets cn block of an mdf file
    @param data: the bytes of the block
    @param vers: mdf file version 
    @param bord: byte order of contents
    @note: not every block actually uses version and byte order but referred for consistency purposes
    @return: a dictionary with the contents
    """    
    if bord == 'little':
        fmtprefix = '<'
    else:
        fmtprefix = '>'
    ncb_ptr,cf_ptr,sde_ptr,db_ptr,ct_ptr,ctp = struct.unpack("{0}IIIIIH".format(fmtprefix),data[4:26])
    ctp_dict = {0:"data",
                1:"time",
                }
    ctp_str = ctp_dict[ctp]
    ssn = data[26:58].rstrip(b'\x00').decode()
    sd = data[58:186].rstrip(b'\x00').decode()
    so,num_b,sdtp = struct.unpack("{0}HHH".format(fmtprefix),data[186:192])
    
    vrv = struct.unpack("?",data[192:193])[0]
    sv_min,sv_max,sv_sr = struct.unpack("{0}ddd".format(fmtprefix),data[193:217])
    lsnt_ptr,dsn_ptr,adbos = struct.unpack("{0}IIH".format(fmtprefix),data[217:227])
    
    ret = {"next_channel_pointer":ncb_ptr,
           "conversion_formula_pointer":cf_ptr,
           "extentions_pointer":sde_ptr,
           "dependency_block_pointer":db_ptr,
           "comment_text_pointer":ct_ptr,
           "channel_type":ctp_str,
           "short_signal_name":ssn,
           "signal_description":sd,
           "bit_offset":so,
           "number_of_bits":num_b,
           "signal_data_type":sdtp,
           "range_valid":vrv,
           "signal_min":sv_min,
           "signal_max":sv_max,
           "sampling_rate":sv_sr,
           "long_signal_name_pointer":lsnt_ptr,
           "display_name_pointer":dsn_ptr,
           "byte_offset":adbos,
           }
    return ret


def _interpret_cc_block(data,vers=3.0,bord='little'):
    """
    interprets cc block of an mdf file
    @param data: the bytes of the block
    @param vers: mdf file version 
    @param bord: byte order of contents
    @note: not every block actually uses version and byte order but referred for consistency purposes
    @return: a dictionary with the contents
    """    
    if bord == 'little':
        fmtprefix = '<'
    else:
        fmtprefix = '>'
    prv = struct.unpack("{0}?".format(fmtprefix),data[4:5])[0]
    ps_min,ps_max = struct.unpack("{0}dd".format(fmtprefix),data[5:21])
    pu = data[21:42].strip(b'\x00').decode()
    ct,si = struct.unpack("{0}HH".format(fmtprefix),data[42:46])
    ct_dict = {0:"parametric,linear",
               1:"tabular with interpolation",
               2:"tabular",
               6:"polynomial function",
               7:"exponential function",
               8:"logarithmic function",
               9:"rational conversion formula",
               10:"ASAM-MCD2 Text Formula",
               11:"ASAM-MCD2 Text Table(COMPU_VTAB)",
               12:"ASAM-MCD2 Text Range Table(COMPU_VTAB_RANGE)",
               132:"date(7Byte struct)",
               133:"time(6Byte struct)",
               2816:"unknown",
               65280:"unknown",
               65535:"1:1 conversion (Int=Phys)"
               }

    ct_str = ct_dict[ct]
    
    si_dict = {"number of parameters":[0,6,7,8,9],
               "number of values":[1,2,11,12],
               "number of characters":[10],}
    parameters = None
    idx = 46

    if ct_str == "parametric,linear":
        parameters = struct.unpack("{0}dd".format(fmtprefix),data[idx:idx+16])
        
    elif ct_str == "unknown":
        pass
    
    elif ct_str == "1:1 conversion (Int=Phys)":
        pass

    elif ct_str == "ASAM-MCD2 Text Table(COMPU_VTAB)":
        parameters = {}
        chunk_length = 40#8Byte Floating Point Number + 32 Byte String , yes the idiot who defined the format did think an index can be a float!
        for i in range(si):
            chunk_strt = idx+(i*chunk_length)
            val = struct.unpack("{0}d".format(fmtprefix),data[chunk_strt:chunk_strt+8])[0]
            txt = data[chunk_strt+8:chunk_strt+40].strip(b'\x00').decode()
            parameters.update({val:txt})
            
    else:
        raise NotImplementedError("Extraction of Parameters for Type {0} not Implemented".format(ct_dict[ct]))

    ret = {"range_valid":prv,
           "signal_min":ps_min,
           "signal_max":ps_max,
           "physical_unit":pu,
           "conversion_type":ct_str,
           "size_information":si_dict,
           "parameters":parameters,
           }        

    return ret


def _interpret_cd_block(data,vers=3.0,bord='little'):
    """
    interprets cd block of an mdf file
    @param data: the bytes of the block
    @param vers: mdf file version 
    @param bord: byte order of contents
    @note: not every block actually uses version and byte order but referred for consistency purposes
    @return: a dictionary with the contents
    """      
    if bord == 'little':
        fmtprefix = '<'
    else:
        fmtprefix = '>'
    dt,num_sd = struct.unpack("{0}HH".format(fmtprefix),data[4:8])
    dp_list = []
    for i in range(num_sd):
        dg_ptr,cg_ptr,ch_ptr = struct.unpack("{0}III".format(fmtprefix),data[8+(i*12):20+(i*12)])
        dp_list.append({"data_group_pointer":dg_ptr,
                        "channel_group_pointer":cg_ptr,
                        "channel_pointer":ch_ptr,
                        })
    ret = {"dependency_type":dt,
           "number_of_dependencies":num_sd,
           "dependencies":dp_list,}
    return ret


def _interpret_ce_block(data,vers=3.0,bord='little'):
    """
    interprets ce block of an mdf file
    @param data: the bytes of the block
    @param vers: mdf file version 
    @param bord: byte order of contents
    @note: not every block actually uses version and byte order but referred for consistency purposes
    @return: a dictionary with the contents
    """     
    if bord == 'little':
        fmtprefix = '<'
    else:
        fmtprefix = '>'
    et_dict = {2:"DIM",
               19:"Vector CAN",
               }
    et_raw = struct.unpack("{0}H".format(fmtprefix),data[4:6])[0]
    et = et_dict(et_raw)
    ret = {"extention_type":et,
           }
    if et == 'DIM':
        nom,addr = struct.unpack("{0}HI".format(fmtprefix),data[6:12])
        desc = data[12:92].strip(b'\x00\x20').decode()
        ecuid = data[92:134].strip(b'\x00\x20').decode()
        ret.update({"number_of_module":nom,
                    "address":addr,
                    "description":desc,
                    "identification_of_ecu":ecuid,
                    })
    elif et == 'Vector CAN':
        can_id,can_ch = struct.unpack("{0}II".format(fmtprefix),data[6:14])
        msg_name = data[14:50].strip(b'\x00\x20').decode()
        snd_name = data[50:86].strip(b'\x00\x20').decode()
        ret.update({"identifier_of_can_message":can_id,
                    "index_of_can_channel":can_ch,
                    "name_of_message":msg_name,
                    "name_of_sender":snd_name,
                    })
    return ret


def _interpret_record(rec,chs,bord):
    vals = []
    for ch in chs:
        bit_offset = ch.get_bit_offset()
        bit_size = ch.get_bit_size()
        byte_offset = ch.get_byte_offset()#did not find any program that actually uses this
        if byte_offset:
            raise NotImplementedError("byte_offset {0} is set but not used".format(byte_offset))
        signal_type = ch.get_signal_type()
        if bit_offset%8:
            raise NotImplementedError("bit_offset cannot be divided by 8")
        offset = int(bit_offset/8)
        if bit_size%8:
            raise NotImplementedError("bit_size cannot be divided by 8")
        size = int(bit_size/8)
        sig_data = rec[offset:offset+size]
        if signal_type == 0:
            #unsigned integer
            fmt = "I"
            if bord == 'little':
                fmtprefix = '<'
                sig_data_just = sig_data.ljust(4,b'\x00')
            else:
                fmtprefix = '>'
                sig_data_just = sig_data.rjust(4,b'\x00')
            val = struct.unpack("{0}{1}".format(fmtprefix,fmt),sig_data_just)[0]
        elif signal_type == 1:
            #signed integer
            fmt = "i"
            if bord == 'little':
                fmtprefix = '<'
                sig_data_just = sig_data.ljust(4,b'\x00')
            else:
                fmtprefix = '>'
                sig_data_just = sig_data.rjust(4,b'\x00')
            val = struct.unpack("{0}{1}".format(fmtprefix,fmt),sig_data_just)[0]
        elif signal_type == 3:
            #float64, e.g. double
            fmt = "d"
            if bord == 'little':
                fmtprefix = '<'
                sig_data_just = sig_data.ljust(8,b'\x00')#just trying
            else:
                fmtprefix = '>'
                sig_data_just = sig_data.rjust(8,b'\x00')
            val = struct.unpack("{0}{1}".format(fmtprefix,fmt),sig_data_just)[0]
        elif signal_type == 7:
            #string
            val = sig_data.rstrip(b'\x00').decode()
        else:
            raise NotImplementedError("unhandled {0}".format(signal_type))
        conversion_formula = ch.get_conversion_formula()
        if conversion_formula != None:
            phy_val = conversion_formula(val)
        else:
            phy_val = val
        if ch.get_channel_type() == "time":
            phy_val = datetime.timedelta(seconds=phy_val)
        vals.append(phy_val)
    return vals
    

class mdf_block():
    
    def __init__(self,fobj,foffset,*args,**kwargs):
        """
        parent class for all block structures in the mdf file
        @param fobj: the file object
        @param foffset: the offset in the file where the block starts 
        @return: the block as an object        
        """
        self.data = bytearray()
        self.block_data = {}
        if fobj:
            if foffset:
                fobj.seek(foffset)
            self.data.extend(fobj.read(4))
            if len(self.data) >= 4:
                block_id = self.data[:2].decode()
                block_size = struct.unpack("H",self.data[2:4])[0]
                self.data.extend(fobj.read(block_size-len(self.data)))
                if len(self.data) != block_size:
                    raise ValueError("Block {0} length invalid block_size={1} len(data)={2}".format(block_id,block_size,len(self.data)))
                else:
                    self.block_data.update({"block_id":block_id})

    def __str__(self):
        return str(self.block_data)

    
class id_block(mdf_block):

    def __init__(self,fobj,foffset=0,*args,**kwargs):
        """
        the id block at the top of each mdf file,
        located at the first 64 bytes,
        there is one id block in one mdf file,
        gives basic file information
        @param fobj: the file object
        @param foffset: the offset in the file where the block starts 
        @return: the block as an object
        """        
        self.block_data = {"block_id":"ID"}
        self.data = fobj.read(64)
        self.block_data.update(_interpret_id_block(self.data))
        self.text = self.block_data.pop("file_identifier")

    def get_version(self):
        return self.block_data['version_number']

    def get_byte_order(self):
        return self.block_data['default_byte_order']

    def __str__(self):
        return self.text


class hd_block(mdf_block):

    def __init__(self,fobj,vers,bord,ignore_channels=[],foffset=64,*args,**kwargs):
        """
        header block for the mdf file
        @param fobj: the file object
        @param foffset: the offset in the file where the block starts, 64 bytes for hd block 
        @param vers: mdf file version 
        @param bord: byte order of contents
        @param ignore_channels: a list of strings which channels are to be ignored, i.e. program specific stuff         
        @return: the block as an object
        """
        super(hd_block,self).__init__(fobj=fobj,foffset=foffset,*args,**kwargs)
        assert(self.block_data["block_id"] == "HD")
        self.block_data.update(_interpret_hd_block(data=self.data,vers=vers,bord=bord))


        self.author = self.block_data.pop("author")
        self.organisation = self.block_data.pop("organisation")
        self.subject = self.block_data.pop("subject")
        self.timestamp = self.block_data.pop("timestamp")

        self.ignore_channels = ignore_channels
        
        self.data_groups = []
        dg_ptr = self.block_data.pop("data_group_pointer")
        while dg_ptr > 0:
            dgb = dg_block(fobj=fobj,vers=vers,bord=bord,foffset=dg_ptr,timestamp=self.timestamp,ignore_channels=self.ignore_channels)
            self.data_groups.append(dgb)
            dg_ptr = dgb.block_data.pop("next_data_group_pointer")       

        self.text = ""
        ct_ptr = self.block_data.pop("comment_text_pointer")
        if ct_ptr:
            self.text = str(tx_block(fobj=fobj,vers=vers,bord=bord,foffset=ct_ptr))

        pb_ptr = self.block_data.pop("program_block_pointer")
        self.program_data = None
        if pb_ptr:
            self.program_data = pr_block(fobj=fobj,vers=vers,bord=bord,foffset=ct_ptr)["data"]


        self.number_of_data_groups = self.block_data.pop("number_of_data_groups")
        assert (self.number_of_data_groups == len(self.data_groups))
  
    def __str__(self):
        return self.text

    def get_data_groups(self):
        return self.data_groups

    def print_data_group_statistics(self):
        data_groups = self.get_data_groups()
        for idx,dg in enumerate(data_groups):
            strt,stp = dg.calc_data_block_range()
            basestr = "Block {0} of {1}".format(idx+1,len(data_groups))
            if strt:
                print("{0}, Raw Data Block from {1:08X} to {2:08X}(included)".format(basestr,strt,stp))
            else:
                print("{0}, No Raw Data Block".format(basestr))
        return
                
    def check_data_block_consistency(self):
        data_groups = self.get_data_groups()
        blocks = []
        for idx,dg in enumerate(data_groups):
            strt,stp = dg.calc_data_block_range()
            if strt:
                blocks.append((strt,stp))
        for idx in range(len(blocks)-1):
            if blocks[idx][1]+1 != blocks[idx+1][0]:
                raise NotImplementedError("Inconsistent Data Blocks [from,to] {0} (X) {1} (X+1)".format(blocks[idx],blocks[idx+1]))
        return True
            
    def print_hierachy(self,pad=0):
        for dg in self.get_data_groups():
            print("{0}{1}".format(pad*" ",dg))
            dg.print_hierachy(pad+4)
        return

    def get_channel_short_names(self):
        ret = []
        for dg in self.get_data_groups():
            sn = dg.get_channel_short_names()
            if sn:
                ret.extend(sn)
        return ret

    def get_channels(self):
        ret = []
        for dg in self.get_data_groups():
            sn = dg.get_channels()
            if sn:
                ret.extend(sn)
        return ret

    def get_data_group_for_channel(self,short_name):
        ret = None
        for dg in self.get_data_groups():
            if short_name in dg.get_channel_short_names():
                ret = dg
                break
        return ret

    def get_channel_by_short_name(self,short_name):
        for dg in self.get_data_groups():
            ch = dg.get_channel_by_short_name(short_name=short_name)
            if ch:
                return ch
        return None

    def get_records_with_timestamp(self,fname,short_names,useabsolutetime=False):
        for dg in self.get_data_groups():
            if useabsolutetime:
                recs = dg.get_records_with_timestamp(fname=fname,short_names=short_names,starttime=self.timestamp)
            else:
                recs = dg.get_records_with_timestamp(fname=fname,short_names=short_names)
            if recs:
                return recs
        return None


class tx_block(mdf_block):

    def __init__(self,fobj,foffset,vers,bord,*args,**kwargs):
        """
        text block in the mdf file
        @param fobj: the file object
        @param foffset: the offset in the file where the block starts 
        @param vers: mdf file version 
        @param bord: byte order of contents         
        @return: the string contained in the text block
        """
        super(tx_block,self).__init__(fobj=fobj,foffset=foffset,*args,**kwargs)
        assert(self.block_data["block_id"] == "TX")
        self.block_data.update(_interpret_tx_block(data=self.data,vers=vers,bord=bord))

    def __str__(self):
        return str(self.block_data['text'])
    

class pr_block(mdf_block):

    def __init__(self,fobj,foffset,vers,bord,*args,**kwargs):
        """
        program specific block in the mdf file
        @param fobj: the file object
        @param foffset: the offset in the file where the block starts 
        @param vers: mdf file version 
        @param bord: byte order of contents         
        @return: the block as an object
        """  
        super(pr_block,self).__init__(fobj=fobj,foffset=foffset,*args,**kwargs)
        assert(self.block_data["block_id"] == "PR")
        self.block_data.update(_interpret_pr_block(data=self.data,vers=vers,bord=bord))

        #is there a __bin__ function to return the binaray self.block_data["data"]


class dg_block(mdf_block):   

    def __init__(self,fobj,foffset,vers,bord,timestamp,ignore_channels=[],*args,**kwargs):
        """
        data group block in the mdf file
        @param fobj: the file object
        @param foffset: the offset in the file where the block starts 
        @param vers: mdf file version 
        @param bord: byte order of contents
        @param timestamp: the timestamp of the file to calculate absolute timestamp later    
        @param ignore_channels: a list of strings which channels are to be ignored, i.e. program specific stuff
        @return: the block as an object        
        """           
        super(dg_block,self).__init__(fobj=fobj,foffset=foffset,*args,**kwargs)
        assert(self.block_data["block_id"] == "DG")
        self.block_data.update(_interpret_dg_block(data=self.data,vers=vers,bord=bord))

        self.ignore_channels = ignore_channels
        self.timestamp=timestamp
        
        self.channel_groups = []
        chgb_ptr = self.block_data.pop("first_channel_group_pointer")
        while chgb_ptr > 0:
            chgb = cg_block(fobj=fobj,vers=vers,bord=bord,foffset=chgb_ptr,ignore_channels=self.ignore_channels)
            self.channel_groups.append(chgb)
            chgb_ptr = chgb.block_data.pop("next_channel_group_pointer")
        #self.channel_groups.sort(key = lambda x: x.record_id)
        if len(self.channel_groups) > 1:
            raise NotImplementedError("This MDF File is unsorted, e.g. contains more than one channel groups in a single data block, ({0} found)")

        self.trigger_block = None
        tb_ptr = self.block_data.pop("trigger_block_pointer")
        if tb_ptr:
            self.trigger_block = tr_block(fobj=fobj,vers=vers,bord=bord,foffset=tb_ptr)

        self.number_of_channel_groups = self.block_data.pop("number_of_channel_groups")
        assert(self.number_of_channel_groups == len(self.channel_groups))
        self.data_block_ptr = self.block_data.pop("data_block_pointer")
        self.number_of_record_ids = self.block_data.pop("number_of_record_ids")

        #dont convert binary block yet - only convert the binary record that is asked in generator later...
        #self.raw_data_to_signal_list(fobj=fobj,bord=bord,timestamp=timestamp,ignore_channels=ignore_channels)

    def get_channel_groups(self):
        return self.channel_groups

    def print_hierachy(self,pad=0):
        for chg in self.get_channel_groups():
            print("{0}{1}".format(pad*" ",chg))
            chg.print_hierachy(pad+4)
        return

    def calc_data_block_size(self):
        #a sorted mdf file contains only one channel group per data group
        size_of_data_block = 0
        for chg in self.get_channel_groups():
            size_of_record = chg.get_record_size()
            number_of_records = chg.get_number_of_records()
            size_of_data_block += (size_of_record * number_of_records)
        return size_of_data_block

    def calc_data_block_range(self):
        strt = self.data_block_ptr
        size = self.calc_data_block_size()
        stp = strt
        if size:
            stp = strt+size-1
        return (strt,stp)
    
    def __str__(self):
        return("Data Block with Raw Data at address {0:08X}".format(self.data_block_ptr))

    def get_data_block_ptr(self):
        return self.data_block_prt
            
#     def raw_data_to_signal_list(self,fobj,bord,timestamp,printdebug=False,ignore_channels=[]):
#         fobj.seek(self.data_block_ptr)
#         for chg in self.get_channel_groups():
#             ignore_it = False
#             for icg in ignore_channels:
#                 #ignore channels that do nothing
#                 if str(chg).startswith(icg):
#                     ignore_it = True
#                     break
#             if not ignore_it:
#                 rec_size = chg.get_record_size()
#                 chs = chg.get_channels()
#                 rec_num = chg.get_number_of_records()
#                 if printdebug:
#                     print("Channel Group: {0}\nNumber of Channels: {1}\nNumber of Records {2}".format(chg,len(chs),rec_num))
#                     print("\n".join(["Channel: {0} Type: {1}".format(ch.short_signal_name,ch.channel_type) for ch in chs]))
#                     
#                 recs = []
#                 #this is the part where data extraction starts
#                 for rec_idx in range(rec_num):
#                     rec = bytearray(fobj.read(rec_size))
#                     vals = _interpret_record(rec=rec,chs=chs,bord=bord)                    
#                     recs.append(vals)
#                 #this would be the end of the functional part
#                 chg.set_records(recs)
#         return
    
    def get_channel_short_names(self,ignore_channels=None):
        if ignore_channels == None:
            ignch = self.ignore_channels
        else:
            ignch = ignore_channels
            
        ret = []
        for chg in self.get_channel_groups():
            sns = chg.get_channel_short_names()
            if sns:
                for sn in sns:
                    ignore_it = False
                    for ign in ignch:
                        if sn.startswith(ign):
                            ignore_it = True
                    if not ignore_it:
                        ret.append(sn)
        return ret

    def get_channel_group_for_channel(self,short_name):
        ret = None
        for cg in self.get_channel_groups():
            if cg.get_channel_short_names():
                ret = cg
                break
        return ret

    def get_channel_by_short_name(self,short_name):
        for cg in self.get_channel_groups():
            ch = cg.get_channel_by_short_name(short_name=short_name)
            if ch:
                return ch
        return None

    def get_records_with_timestamp(self,fname,short_names,starttime=None):
        for cg in self.get_channel_groups():
            #print(cg)
            recs = cg.get_records_with_timestamp(fname=fname,foffset=self.data_block_ptr,short_names=short_names,starttime=starttime)
            if recs:
                return recs
        return None
    
            
class cg_block(mdf_block):
    
    def __init__(self,fobj,foffset,vers,bord,ignore_channels=[],*args,**kwargs):
        """
        channel group block in the mdf file
        @param fobj: the file object
        @param foffset: the offset in the file where the block starts 
        @param vers: mdf file version 
        @param bord: byte order of contents    
        @param ignore_channels: a list of strings which channels are to be ignored, i.e. program specific stuff
        @return: the block as an object         
        """ 
        super(cg_block,self).__init__(fobj=fobj,foffset=foffset,*args,**kwargs)
        assert(self.block_data["block_id"] == "CG")
        self.block_data.update(_interpret_cg_block(data=self.data,vers=vers,bord=bord))

        self.ignore_channels = ignore_channels#needed to filter out INCA related program SPAM
        self.bord = bord
        self.records = []
        self.channels = []
        self.time_channel_idx = None
        chb_ptr = self.block_data.pop("first_channel_pointer")
        while chb_ptr > 0:
            chb = cn_block(fobj=fobj,vers=vers,bord=bord,foffset=chb_ptr)
            self.channels.append(chb)
            chb_ptr = chb.block_data.pop("next_channel_pointer")
        for idx,ch in enumerate(self.channels):
            if ch.get_channel_type() == "time":
                self.time_channel_idx = idx
                break
        assert(self.time_channel_idx != None)
        self.text = ""
        ct_ptr = self.block_data.pop("comment_text_pointer")
        if ct_ptr:
            self.text = str(tx_block(fobj=fobj,vers=vers,bord=bord,foffset=ct_ptr))

        self.record_id = self.block_data.pop("record_id")

        self.number_of_channels = self.block_data.pop("number_of_channels")
        assert(self.number_of_channels == len(self.channels))
        self.record_size = self.block_data.pop("record_size")
        self.number_of_records = self.block_data.pop("number_of_records")

    def __str__(self):
        return self.text
        
    def get_channels(self):
        return self.channels

    def get_record_size(self):
        return self.record_size

    def get_number_of_records(self):
        return self.number_of_records

    def get_time_channel_index(self):
        return self.time_channel_idx

    def get_time_channel(self):
        return self.channels[self.get_time_channel_index()]

    def get_data_channels(self):
        ret = []
        for ch in self.get_channels():
            if ch.get_channel_type == "data":
                ret.append(ch)
        return ret

    def set_records(self,recs):
        self.records = recs
        return

    def get_channel_by_short_name(self,short_name):
        for ch in self.get_channels():
            if ch.get_short_name().startswith(short_name):
                return ch
        return None

    def get_channel_index(self,short_name):
        for idx,ch in enumerate(self.get_channels()):
            if ch.get_short_name().startswith(short_name):
                return idx
        return None

    def get_channel_short_name_by_query(self,q):
        for ch in self.get_channels():
            chsn = ch.get_short_name()
            if chsn.startswith(q):
                return chsn
        return None
    
    #this function needs to implement the binary data transformation    
    def get_records_with_timestamp(self,fname,foffset,short_names=None,starttime=None):
        rec_size = self.get_record_size()
        chs = self.get_channels()
        rec_num = self.get_number_of_records()
        #generator
        channel_names = []
        channel_idxs = []
        if short_names:
            if isinstance(short_names,str):
                #single data channel
                chsn = self.get_channel_short_name_by_query(short_names)
                if chsn:
                    channel_names.append(chsn)
            elif isinstance(short_names,list):
                #more than one data channel
                for short_name in short_names:
                    chsn = self.get_channel_short_name_by_query(short_name)
                    if chsn:
                        channel_names.append(chsn)
        else:
            channel_names = self.get_channel_short_names()
        

        for chn in channel_names:
            channel_idxs.append(self.get_channel_index(short_name=chn))
        #prepared list of names and list of indexes
                
        time_channel_index = self.get_time_channel_index()
        
        if foffset:
            with open(fname,'rb') as f:
                f.seek(foffset)
                for rec_idx in range(rec_num):
                    rec = bytearray(f.read(rec_size))
                    vals = _interpret_record(rec=rec,chs=chs,bord=self.bord)
                    timestamp = vals.pop(time_channel_index)
                    
                    if starttime:
                        ret = {timestamp+starttime:vals}
                    else:
                        ret = {timestamp:vals}
                    yield ret 
        else:
            return None
        
        
#         for i in range(self.get_number_of_records()):
#             this_record_dict = {}
#             for chname,chidx in zip(channel_names,channel_idxs):
#                 this_record_dict.update({chname:self.records[i][chidx]})
#                 
#             if starttime:
#                 rec = {self.records[i][time_channel_index]+starttime:this_record_dict}
#             else:
#                 rec = {self.records[i][time_channel_index]:this_record_dict}
#             yield rec


    def channel_in_group(self,short_name):
        if self.get_channel_by_short_name(short_name=short_name):
            return True
        else:
            return False
            
    def get_records(self):
        return self.records

    def get_channel_short_names(self):
        ret = []
        for ch in self.get_channels():
            if ch.get_channel_type() == "data":
                sn = ch.get_short_name()
                if sn:
                    ret.append(sn)
        return ret

    def print_hierachy(self,pad=0):
        """
        convenience function
        """
        print("{0}record_id {1}".format(pad*" ",self.record_id))
        print("{0}record_size {1} in bytes".format(pad*" ",self.record_size))
        print("{0}number_of_records {1}".format(pad*" ",self.number_of_records))
        print("{0}Overall Size {1} bytes".format(pad*" ",self.record_size*self.number_of_records))
        for ch in self.get_channels():
            print("{0}{1}".format(pad*" ",ch))
            ch.print_hierachy(pad+4)
        return

    
class tr_block(mdf_block):
   
    def __init__(self,fobj,foffset,vers,bord,*args,**kwargs):
        """
        trigger block in the mdf file
        @param fobj: the file object
        @param foffset: the offset in the file where the block starts 
        @param vers: mdf file version 
        @param bord: byte order of contents    
        @return: the block as an object           
        """
        super(tr_block,self).__init__(fobj=fobj,foffset=foffset,*args,**kwargs)
        assert(self.block_data["block_id"] == "TR")
        self.block_data.update(_interpret_tr_block(data=self.data,vers=vers,bord=bord))

        self.text = None
        ct_ptr = self.block_data.pop("comment_text_pointer")
        if ct_ptr:
            self.text = str(tx_block(fobj=fobj,vers=vers,bord=bord,foffset=ct_ptr))

        self.number_of_trigger_events = self.block_data.pop("number_of_trigger_events")
        self.trigger_events = self.block_data.pop("trigger_events")

    def __str__(self):
        return self.text    
        

class sr_block(mdf_block):
 
    def __init__(self,fobj,foffset,vers,bord,*args,**kwargs):
        """
        sample reduce block in the mdf file
        @param fobj: the file object
        @param foffset: the offset in the file where the block starts 
        @param vers: mdf file version 
        @param bord: byte order of contents    
        @return: the block as an object                
        """  
        super(sr_block,self).__init__(fobj=fobj,foffset=foffset,*args,**kwargs)
        assert(self.block_data["block_id"] == "SR")
        self.block_data.update(_interpret_sr_block(data=self.data,vers=vers,bord=bord))

        self.data_block_pointer = self.block_data.pop("data_block_pointer")
        self.number_of_reduced_samples = self.block_data.pop("number_of_reduced_samples")
        self.length_of_time_interval = self.block_data.pop("length_of_time_interval")


class cn_block(mdf_block):   
    
    def __init__(self,fobj,foffset,vers,bord,*args,**kwargs):
        """
        channel block in the mdf file
        @param fobj: the file object
        @param foffset: the offset in the file where the block starts 
        @param vers: mdf file version 
        @param bord: byte order of contents    
        @return: the block as an object           
        """   
        super(cn_block,self).__init__(fobj=fobj,foffset=foffset,*args,**kwargs)
        assert(self.block_data["block_id"] == "CN")
        self.block_data.update(_interpret_cn_block(data=self.data,vers=vers,bord=bord))

        self.conversion_formula = None
        cf_ptr = self.block_data.pop("conversion_formula_pointer")
        if cf_ptr:
            self.conversion_formula = cc_block(fobj=fobj,vers=vers,bord=bord,foffset=cf_ptr).get_conversion_function()
            
        self.extentions = None
        sde_ptr = self.block_data.pop("extentions_pointer")
        if sde_ptr:
            self.extentions = ce_block(fobj=fobj,vers=vers,bord=bord,foffset=sde_ptr)
        self.dependencies = None
        db_ptr = self.block_data.pop("dependency_block_pointer")
        if db_ptr:
            self.dependencies = cd_block(fobj=fobj,vers=vers,bord=bord,foffset=db_ptr)
        self.text = ""
        ct_ptr = self.block_data.pop("comment_text_pointer")
        if ct_ptr:
            self.text = str(tx_block(fobj=fobj,vers=vers,bord=bord,foffset=ct_ptr))

        self.channel_type = self.block_data.pop("channel_type")
        self.short_signal_name = self.block_data.pop("short_signal_name")
        self.signal_description = self.block_data.pop("signal_description")
        self.bit_offset = self.block_data.pop("bit_offset")
        self.number_of_bits = self.block_data.pop("number_of_bits")
        self.byte_offset = self.block_data.pop("byte_offset")
        self.signal_data_type = self.block_data.pop("signal_data_type")
        self.range_valid = self.block_data.pop("range_valid")
        self.signal_min = self.block_data.pop("signal_min")
        self.signal_max = self.block_data.pop("signal_max")
        self.sampling_rate = self.block_data.pop("sampling_rate")
        self.long_signal_name = None
        self.display_name = None

        
    def __str__(self):
        return self.text

    def get_bit_offset(self):
        return self.bit_offset

    def get_bit_size(self):
        return self.number_of_bits

    def get_byte_offset(self):
        return self.byte_offset

    def get_signal_type(self):
        return self.signal_data_type

    def get_short_name(self):
        return self.short_signal_name

    def get_conversion_formula(self):
        return self.conversion_formula

    def get_channel_type(self):
        return self.channel_type

    
    def print_hierachy(self,pad=0):
        print("{0}str(self) {1}".format(pad*" ",str(self)))
        print("{0}short_signal_name {1}".format(pad*" ",self.short_signal_name))
        print("{0}description {1}".format(pad*" ",self.signal_description))
        print("{0}byte_offset {1} bit_offset {2} bits {3} type {4}".format(pad*" ",self.byte_offset,self.bit_offset,self.number_of_bits,self.signal_data_type))
        return



class cc_block(mdf_block):

    def __init__(self,fobj,foffset,vers,bord,*args,**kwargs):
        """
        channel conversion block in the mdf file
        @param fobj: the file object
        @param foffset: the offset in the file where the block starts 
        @param vers: mdf file version 
        @param bord: byte order of contents    
        @return: the block as an object          
        """
        super(cc_block,self).__init__(fobj=fobj,foffset=foffset,*args,**kwargs)
        assert(self.block_data["block_id"] == "CC")
        self.block_data.update(_interpret_cc_block(data=self.data,vers=vers,bord=bord))

        self.range_valid = self.block_data.pop("range_valid")
        self.signal_min = self.block_data.pop("signal_min")
        self.signal_max = self.block_data.pop("signal_max")
        self.physical_unit = self.block_data.pop("physical_unit")
        self.conversion_type = self.block_data.pop("conversion_type")
        self.size_information = self.block_data.pop("size_information")
        self.parameters = self.block_data.pop("parameters")

    def get_conversion_function(self):
        if self.conversion_type == "parametric,linear":
            assert(isinstance(self.parameters,tuple))
            return lambda x: ((x*self.parameters[1]) + self.parameters[0])
        
        elif self.conversion_type == "unknown":
            return None
        
        elif self.conversion_type == "ASAM-MCD2 Text Table(COMPU_VTAB)":
            return lambda x: self.parameters[x]
        
        elif self.conversion_type == "1:1 conversion (Int=Phys)":
            return None
            
        else:
            raise NotImplementedError("Conversion Type {0} not handled".format(self.conversion_type))
        

class cd_block(mdf_block):
    
    def __init__(self,fobj,foffset,vers,bord,*args,**kwargs):
        """
        channel dependencies block in the mdf file
        @param fobj: the file object
        @param foffset: the offset in the file where the block starts 
        @param vers: mdf file version 
        @param bord: byte order of contents    
        @return: the block as an object          
        """
        super(cd_block,self).__init__(fobj=fobj,foffset=foffset,*args,**kwargs)
        assert(self.block_data["block_id"] == "CD")
        self.block_data.update(_interpret_cd_block(data=self.data,vers=vers,bord=bord))

        self.dependency_type = self.block_data.pop("dependency_type")
        self.number_of_dependencies = self.block_data.pop("number_of_dependencies")
        self.dependencies = self.block_data.pop("dependencies")
        assert(self.number_of_dependencies == len(self.dependencies))


class ce_block(mdf_block):

    def __init__(self,fobj,foffset,vers,bord,*args,**kwargs):
        """
        channel extentions block in the mdf file
        @param fobj: the file object
        @param foffset: the offset in the file where the block starts 
        @param vers: mdf file version 
        @param bord: byte order of contents    
        @return: the block as an object          
        """
        super(ce_block,self).__init__(fobj=fobj,foffset=foffset,*args,**kwargs)
        assert(self.block_data["block_id"] == "CE")
        self.block_data.update(_interpret_ce_block(data=self.data,vers=vers,bord=bord))



class mdf():
    
    def __init__(self,fname=None,ignore_channels=["VG","CalibrationRecordingSingleShotGroup","$"]):
        """
        measure data file class
        @param fname: path to file
        @param ignore_channels: a list of strings which channels are to be ignored, i.e. program specific stuff
        @return: the mdf object   
        """
        self.idblock = None
        self.hdblock = None
        self.fname = fname
        if self.fname:
            self.read_mdf_file(fname=self.fname,ignore_channels=ignore_channels)


    def read_mdf_file(self,fname,ignore_channels):
        with open(fname,'rb') as f:
            try:
                self.idblock = id_block(f)
                #extract version and byte order for further block interpretation
                self.version = self.idblock.get_version()
                self.byte_order = self.idblock.get_byte_order()
                
                self.hdblock = hd_block(fobj=f,vers=self.version,bord=self.byte_order,ignore_channels=ignore_channels)
                
            except EOFError:
                print("EOF")
        
        return

    def get_channel_short_names(self):
        return self.hdblock.get_channel_short_names()

    def get_channel_by_short_name(self,short_name):
        return self.hdblock.get_channel_by_short_name(short_name=short_name)

    def get_records_with_timestamp(self,short_names=None,useabsolutetime=False):
        return self.hdblock.get_records_with_timestamp(fname=self.fname,short_names=short_names,useabsolutetime=useabsolutetime)


    

def selftest(testmode="read_mdf",fname="test.mdf"):
    from mdftools import to_csv_file,to_xlsx_file
    if testmode == "mdf2csv":
        a = mdf(fname=fname)
        c = fname[:-3] + "csv" 
        to_csv_file(a,c,useabsolutetime=True)
    elif testmode == "mdf2xlsx":
        a = mdf(fname=fname)
        c = fname[:-3] + "xlsx" 
        to_xlsx_file(a,c,useabsolutetime=True)
        

    return

if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-c", "--command", dest="command", default="mdf2xlsx",
                      help="COMMAND to execute", metavar="COMMAND")
    parser.add_option("-f", "--file", dest="fname", default="recorder1-001.mdf",
                      help="FILE to use", metavar="FILE")    
    (options, args) = parser.parse_args()
 
    selftest(testmode = options.command,fname=options.fname)
