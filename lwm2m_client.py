import time
import struct
import socket
import select
import random
from threading import Thread
from assist.coap import CoAP
from assist.color_print import color
from assist.excel_read import read_xls
from assist.lwm2m import LWM2M

udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

# 提取需要用到的参数
values = read_xls(file='param.xls', sheet='LWM2M', column=1)
serverIp = values[1]
serverPort = int(values[2])
empower = values[3]
# 提取需要用到的属性
# Manufacturer_3_0_0 = values[4]  # String
# ModelNumber_3_0_1 = values[5]  # String
# SerialNumber_3_0_2 = values[6]  # String
# FirmwareVersion_3_0_3 = values[7]  # String
# BatteryLevel_3_0_9 = int(values[8])  # Int64
# MemoryFree_3_0_10 = int(values[9])  # Int64
# ErrorCode_3_0_11 = int(values[10])  # Int64
# CurrentTime_3_0_13 = int(values[11])  # Date
# UTCOffset_3_0_14 = values[12]  # String
# Timezone_3_0_15 = values[13]  # String
# SupportedBindingandModes_3_0_16 = values[14]  # String
# DeviceType_3_0_17 = values[15]  # String
# HardwareVersion_3_0_18 = values[16]  # String
# SoftwareVersion_3_0_19 = values[17]  # String
# BatteryStatus_3_0_20 = int(values[18])  # Int64
# MemoryTotal_3_0_21 = int(values[19])  # Int64
# Latitude_6_0_0 = values[20]  # Float64
# Longitude_6_0_1 = values[21]  # Float64
# Timestamp_6_0_5 = int(values[22])  # Date
# UpdateSupportedObjects_9_0_8 = int(values[23])  # Boolean
# Order_2053_0_0 = int(values[24])  # Int64
# AnalogOutputCurrentValue_3203_0_5650 = values[25]  # Float64
MinMeasuredValue_3303_0_5601 = values[26]  # Float64
# MaxMeasuredValue_3303_0_5602 = values[27]  # Float64
SensorValue_3303_0_5700 = values[28]  # Float64
SensorUnits_3303_0_5701 = values[29]  # String
SetPointValue_3308_0_5900 = values[30]

# token缓存，当全部value都不为空时，开始周期性发送CON(上报数据)
token_buffer = {
                # '/3/0': b'',
                # '/6/0': b'',
                # '/9/0': b'',
                # '/2053/0': b'',
                # '/3203/0': b'',
                '/3303/0': b'',
                '/3308/0': b''
                }


# int转bytes
def intTobytes(integer):
    if integer <= 0xff:
        return struct.pack('!B', integer)
    elif 0xff < integer <= 0xffff:
        return struct.pack('!H', integer)
    elif 0xffff < integer <= 0xffffffff:
        return struct.pack('!L', integer)
    else:
        raise ('输入参数值过大')


# lwm2m设备心跳维护
def lwm2m_echo(addr, empower):
    while True:
        time.sleep(20)
        _boot_header = CoAP(type="CON",
                            code="POST",
                            msg_id=random.randint(60000, 65000),
                            token=bytes.fromhex("".join([random.choice("0123456789abcdef") for i in range(16)])),
                            options=[("Uri-Path", "rd"),
                                     ("Uri-Path", empower.split(';')[0])])
        _boot = bytes(_boot_header)
        udp_socket.sendto(_boot, addr)
        print(color.cyan('已发送心跳报文'))


# lwm2m设备数据上报
def lwm2m_upload(addr):
    while True:
        time.sleep(10)
        if (token_buffer['/3303/0'] != b'') and (token_buffer['/3308/0'] != b''):

            # /3303/0
            _non = bytes(CoAP(type="CON",
                              code="2.05 Content",
                              msg_id=random.randint(30000, 60000),
                              token=token_buffer['/3303/0'],
                              options=[("Observe", b'\x0a'), ("Content-Format", b'\x2d\x16')],
                              paymark=b'\xff'))
            _payload = LWM2M(id=5601, value=struct.pack('!d', MinMeasuredValue_3303_0_5601))
            _send = _non + _payload
            # udp_socket.sendto(_send, addr)
            time.sleep(2)

            # /3308/0
            _non = bytes(CoAP(type="CON",
                              code="2.05 Content",
                              msg_id=random.randint(30000, 60000),
                              token=token_buffer['/3308/0'],
                              options=[("Observe", b'\x0a'), ("Content-Format", b'\x2d\x16')],
                              paymark=b'\xff'))
            _payload = LWM2M(id=5900, value=struct.pack('!d', SetPointValue_3308_0_5900))
            _send = _non + _payload
            # udp_socket.sendto(_send, addr)
            time.sleep(2)

if __name__ == '__main__':

    _boot_header = CoAP(type="CON",
                        code="POST",
                        msg_id=random.randint(1000, 1999),
                        token=bytes.fromhex("".join([random.choice("0123456789abcdef") for i in range(16)])),
                        options=[("Uri-Path", "rd"),
                                 ("Content-Format", "("),
                                 ("Uri-Query", "b=U"),
                                 ("Uri-Query", "lwm2m=1.0"),
                                 ("Uri-Query", "lt=30"),
                                 ("Uri-Query", "ep=" + empower)],
                        paymark=b'\xff')
    _boot_payload = '</>;rt="oma.lwm2m", </1/0>, </3303/0>, </3308/0>'.encode()
    _boot = bytes(_boot_header) + _boot_payload
    udp_socket.sendto(_boot, (serverIp, serverPort))
    print(empower)
    print(color.cyan('已发送上线报文'))

    a = Thread(target=lwm2m_echo, args=((serverIp, serverPort), empower))
    a.setDaemon(True)
    a.start()

    b = Thread(target=lwm2m_upload, args=((serverIp, serverPort),))
    b.setDaemon(True)
    b.start()

    inputs = [udp_socket]
    while True:
        rs, ws, es = select.select(inputs, [], [])  # 监听inputs中的套接字，接收到数据时通过轮询定位套接字
        for r in rs:
            if r is udp_socket:
                _recv, _addr = udp_socket.recvfrom(86400)
                try:
                    _coap_recv = CoAP(_recv)  # 将接收到的字节转化为CoAP型
                except:
                    continue
                _type = _coap_recv.type  # Type
                _code = _coap_recv.code  # Code
                _msg_id = _coap_recv.msg_id  # Message ID
                _token = _coap_recv.token  # Token
                _options = _coap_recv.options  # Options
                _options_list = []
                for n in _options:
                    _options_list.append(n[1])
                try:
                    _load = _coap_recv.load  # 负载信息
                except:
                    _load = None  # 如果没有负载信息则为None
                # 收到CON请求
                if _type == 0:
                    # code为GET(对应平台“读”操作)
                    if _code == 1:

                        # /3308
                        if _options_list[0] == b'3308' and _options_list[1] == b'(':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x28')],
                                              paymark=b'\xff'))
                            _payload = '''</3308>, </3308/0>,</3308/0/5900>'''.encode()
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)


                        # /3308/0
                        elif _options_list[0] == b'' and _options_list[1] == b'3308' and _options_list[2] == b'0':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Observe", b'\x08'), ("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=5900, value=struct.pack('!d', SetPointValue_3308_0_5900))
                            _send = _ack + _payload

                            udp_socket.sendto(_send, _addr)
                            token_buffer['/3308/0'] = _token

                        # /3308/0/5900
                        elif _options_list[0] == b'3308' and _options_list[1] == b'0' and _options_list[2] == b'5900':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=5900, value=struct.pack('!d', SetPointValue_3308_0_5900))

                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)

                    # code为POST(对应平台“执行”操作)
                    elif _code == 2:
                        _ack = bytes(CoAP(type="ACK",
                                          code="2.04 Changed",
                                          msg_id=_msg_id,
                                          token=_token))
                        _send = _ack
                        udp_socket.sendto(_send, _addr)

                    # 收到PUT(对应平台“写”操作)
                    elif _code == 3:
                        _ack = bytes(CoAP(type="ACK",
                                          code="2.04 Changed",
                                          msg_id=_msg_id,
                                          token=_token))
                        _send = _ack
                        if _coap_recv:
                            if _code == 3:

                                print(color.magenta("收到写命令报文"))

                        # udp_socket.sendto(_send, _addr)

                # 收到ACK应答
                elif _type == 2:
                    # code为2.01 Created
                    if _code == 65:
                        print(color.yellow('收到上线回应'))
