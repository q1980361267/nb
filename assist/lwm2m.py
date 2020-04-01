from scapy.fields import *
from scapy.packet import *


# LWM2M头部
class LWM2M_Header(Packet):
    __slots__ = ["content_format"]
    name = "LWM2M Header"
    fields_desc = [BitField("type_of_identifier", 3, 2),
                   BitField("len_of_identifier", None, 1),
                   BitField("len_of_length", None, 2),
                   BitField("value_of_length", None, 3),
                   ]


# 构造LWM2M报文，输入参数有两个：id(int)和value(bytes)
def LWM2M(type=3, id=0, value=b''):
    _value_len = len(value)  # value长度
    if id < 256:
        _id_len = 0  # 表示identifier长度为1个字节
        _body_id = struct.pack('!B', id)
    else:
        _id_len = 1  # 表示identifier长度为2个字节
        _body_id = struct.pack('!H', id)
    if _value_len < 8:
        _len_len = 0  # value长度所占字节大小
        _header = bytes(LWM2M_Header(type_of_identifier=type, len_of_identifier=_id_len, len_of_length=_len_len, value_of_length=_value_len))
        _body_length = b''  # value长度小于8时，不需要该字段
    else:
        _len_len = 1  # value长度所占字节大小
        _header = bytes(LWM2M_Header(type_of_identifier=type, len_of_identifier=_id_len, len_of_length=_len_len,
                                     value_of_length=0))
        _body_length = struct.pack('!B', _value_len)

    _lwm2m = _header + _body_id + _body_length + value
    return _lwm2m
