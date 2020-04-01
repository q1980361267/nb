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
Manufacturer_3_0_0 = values[4]  # String
ModelNumber_3_0_1 = values[5]  # String
SerialNumber_3_0_2 = values[6]  # String
FirmwareVersion_3_0_3 = values[7]  # String
BatteryLevel_3_0_9 = int(values[8])  # Int64
MemoryFree_3_0_10 = int(values[9])  # Int64
ErrorCode_3_0_11 = int(values[10])  # Int64
CurrentTime_3_0_13 = int(values[11])  # Date
UTCOffset_3_0_14 = values[12]  # String
Timezone_3_0_15 = values[13]  # String
SupportedBindingandModes_3_0_16 = values[14]  # String
DeviceType_3_0_17 = values[15]  # String
HardwareVersion_3_0_18 = values[16]  # String
SoftwareVersion_3_0_19 = values[17]  # String
BatteryStatus_3_0_20 = int(values[18])  # Int64
MemoryTotal_3_0_21 = int(values[19])  # Int64
Latitude_6_0_0 = values[20]  # Float64
Longitude_6_0_1 = values[21]  # Float64
Timestamp_6_0_5 = int(values[22])  # Date
UpdateSupportedObjects_9_0_8 = int(values[23])  # Boolean
Order_2053_0_0 = int(values[24])  # Int64
AnalogOutputCurrentValue_3203_0_5650 = values[25]  # Float64
MinMeasuredValue_3303_0_5601 = values[26]  # Float64
MaxMeasuredValue_3303_0_5602 = values[27]  # Float64
SensorValue_3303_0_5700 = values[28]  # Float64
SensorUnits_3303_0_5701 = values[29]  # String

# token缓存，当全部value都不为空时，开始周期性发送CON(上报数据)
token_buffer = {'/3/0': b'',
                '/6/0': b'',
                '/9/0': b'',
                '/2053/0': b'',
                '/3203/0': b'',
                '/3303/0': b''}


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
        if (token_buffer['/3/0'] != b'') \
                and (token_buffer['/6/0'] != b'') \
                and (token_buffer['/9/0'] != b'') \
                and (token_buffer['/2053/0'] != b'') \
                and (token_buffer['/3203/0'] != b'') \
                and (token_buffer['/3303/0'] != b''):
            # /3/0
            _non = bytes(CoAP(type="CON",
                              code="2.05 Content",
                              msg_id=random.randint(30000, 60000),
                              token=token_buffer['/3/0'],
                              options=[("Observe", b'\x05'), ("Content-Format", b'\x2d\x16')],
                              paymark=b'\xff'))
            _payload = LWM2M(id=0, value=Manufacturer_3_0_0.encode()) + \
                       LWM2M(id=1, value=ModelNumber_3_0_1.encode()) + \
                       LWM2M(id=2, value=SerialNumber_3_0_2.encode()) + \
                       LWM2M(id=3, value=FirmwareVersion_3_0_3.encode()) + \
                       LWM2M(id=9, value=intTobytes(BatteryLevel_3_0_9)) + \
                       LWM2M(id=10, value=intTobytes(MemoryFree_3_0_10)) + \
                       LWM2M(type=2, id=11, value=LWM2M(type=1, id=0, value=intTobytes(ErrorCode_3_0_11))) + \
                       LWM2M(id=13, value=struct.pack('!L', CurrentTime_3_0_13)) + \
                       LWM2M(id=14, value=UTCOffset_3_0_14.encode()) + \
                       LWM2M(id=15, value=Timezone_3_0_15.encode()) + \
                       LWM2M(id=16, value=SupportedBindingandModes_3_0_16.encode()) + \
                       LWM2M(id=17, value=DeviceType_3_0_17.encode()) + \
                       LWM2M(id=18, value=HardwareVersion_3_0_18.encode()) + \
                       LWM2M(id=19, value=SoftwareVersion_3_0_19.encode()) + \
                       LWM2M(id=20, value=intTobytes(BatteryStatus_3_0_20)) + \
                       LWM2M(id=21, value=intTobytes(MemoryTotal_3_0_21))
            _send = _non + _payload
            udp_socket.sendto(_send, addr)
            time.sleep(2)
            # /6/0
            _non = bytes(CoAP(type="CON",
                              code="2.05 Content",
                              msg_id=random.randint(30000, 60000),
                              token=token_buffer['/6/0'],
                              options=[("Observe", b'\x08'), ("Content-Format", b'\x2d\x16')],
                              paymark=b'\xff'))
            _payload = LWM2M(id=0, value=struct.pack('!d', Latitude_6_0_0)) + \
                       LWM2M(id=1, value=struct.pack('!d', Longitude_6_0_1)) + \
                       LWM2M(id=5, value=struct.pack('!L', Timestamp_6_0_5))
            _send = _non + _payload
            udp_socket.sendto(_send, addr)
            time.sleep(2)
            # /9/0
            _non = bytes(CoAP(type="CON",
                              code="2.05 Content",
                              msg_id=random.randint(30000, 60000),
                              token=token_buffer['/9/0'],
                              options=[("Observe", b'\x11'), ("Content-Format", b'\x2d\x16')],
                              paymark=b'\xff'))
            _payload = LWM2M(id=8, value=intTobytes(UpdateSupportedObjects_9_0_8))  # 1代表true
            _send = _non + _payload
            udp_socket.sendto(_send, addr)
            time.sleep(2)
            # /2053/0
            _non = bytes(CoAP(type="CON",
                              code="2.05 Content",
                              msg_id=random.randint(30000, 60000),
                              token=token_buffer['/2053/0'],
                              options=[("Observe", b'\x11'), ("Content-Format", b'\x2d\x16')],
                              paymark=b'\xff'))
            _payload = LWM2M(id=0, value=intTobytes(Order_2053_0_0))
            _send = _non + _payload
            udp_socket.sendto(_send, addr)
            time.sleep(2)
            # /3203/0
            _non = bytes(CoAP(type="CON",
                              code="2.05 Content",
                              msg_id=random.randint(30000, 60000),
                              token=token_buffer['/3203/0'],
                              options=[("Observe", b'\x11'), ("Content-Format", b'\x2d\x16')],
                              paymark=b'\xff'))
            _payload = LWM2M(id=5650, value=struct.pack('!d', AnalogOutputCurrentValue_3203_0_5650))
            _send = _non + _payload
            udp_socket.sendto(_send, addr)
            time.sleep(2)
            # /3303/0
            _non = bytes(CoAP(type="CON",
                              code="2.05 Content",
                              msg_id=random.randint(30000, 60000),
                              token=token_buffer['/3303/0'],
                              options=[("Observe", b'\x0a'), ("Content-Format", b'\x2d\x16')],
                              paymark=b'\xff'))
            _payload = LWM2M(id=5601, value=struct.pack('!d', MinMeasuredValue_3303_0_5601)) + \
                       LWM2M(id=5602, value=struct.pack('!d', MaxMeasuredValue_3303_0_5602)) + \
                       LWM2M(id=5700, value=struct.pack('!d', SensorValue_3303_0_5700)) + \
                       LWM2M(id=5701, value=SensorUnits_3303_0_5701.encode())
            _send = _non + _payload
            udp_socket.sendto(_send, addr)
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
    _boot_payload = '</>;rt="oma.lwm2m", </1/0>, </3/0>, </6/0>, </9/0>, </2053/0>, </3203/0>, </3303/0>'.encode()
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
                        # /3
                        if _options_list[0] == b'3' and _options_list[1] == b'(':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x28')],
                                              paymark=b'\xff'))
                            _payload = '''</3>, </3/0>, </3/0/0>, </3/0/1>, </3/0/2>, </3/0/3>, </3/0/9>, </3/0/10>, </3/0/11>, </3/0/13>, </3/0/14>, </3/0/15>, </3/0/16>, </3/0/17>, </3/0/18>, </3/0/19>, </3/0/20>, </3/0/21>, </3/0/23>'''.encode()
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /6
                        elif _options_list[0] == b'6' and _options_list[1] == b'(':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x28')],
                                              paymark=b'\xff'))
                            _payload = '''</6>, </6/0>, </6/0/0>, </6/0/1>, </6/0/5>'''.encode()
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /9
                        elif _options_list[0] == b'9' and _options_list[1] == b'(':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x28')],
                                              paymark=b'\xff'))
                            _payload = '''</9>, </9/0>, </9/0/8>'''.encode()
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /2053
                        elif _options_list[0] == b'2053' and _options_list[1] == b'(':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x28')],
                                              paymark=b'\xff'))
                            _payload = '''</2053>, </2053/0>, </2053/0/0>'''.encode()
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3203
                        elif _options_list[0] == b'3203' and _options_list[1] == b'(':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x28')],
                                              paymark=b'\xff'))
                            _payload = '''</3203>, </3203/0>, </3203/0/5650>'''.encode()
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3303
                        elif _options_list[0] == b'3303' and _options_list[1] == b'(':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x28')],
                                              paymark=b'\xff'))
                            _payload = '''<3303/0/5701>，</3303/0/5700>'''.encode()
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3/0
                        elif _options_list[0] == b'' and _options_list[1] == b'3' and _options_list[2] == b'0':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Observe", b'\x03'), ("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=0, value=Manufacturer_3_0_0.encode()) + \
                                       LWM2M(id=1, value=ModelNumber_3_0_1.encode()) + \
                                       LWM2M(id=2, value=SerialNumber_3_0_2.encode()) + \
                                       LWM2M(id=3, value=FirmwareVersion_3_0_3.encode()) + \
                                       LWM2M(id=9, value=intTobytes(BatteryLevel_3_0_9)) + \
                                       LWM2M(id=10, value=intTobytes(MemoryFree_3_0_10)) + \
                                       LWM2M(type=2, id=11,
                                             value=LWM2M(type=1, id=0, value=intTobytes(ErrorCode_3_0_11))) + \
                                       LWM2M(id=13, value=struct.pack('!L', CurrentTime_3_0_13)) + \
                                       LWM2M(id=14, value=UTCOffset_3_0_14.encode()) + \
                                       LWM2M(id=15, value=Timezone_3_0_15.encode()) + \
                                       LWM2M(id=16, value=SupportedBindingandModes_3_0_16.encode()) + \
                                       LWM2M(id=17, value=DeviceType_3_0_17.encode()) + \
                                       LWM2M(id=18, value=HardwareVersion_3_0_18.encode()) + \
                                       LWM2M(id=19, value=SoftwareVersion_3_0_19.encode()) + \
                                       LWM2M(id=20, value=intTobytes(BatteryStatus_3_0_20)) + \
                                       LWM2M(id=21, value=intTobytes(MemoryTotal_3_0_21))
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                            token_buffer['/3/0'] = _token
                        # /6/0
                        elif _options_list[0] == b'' and _options_list[1] == b'6' and _options_list[2] == b'0':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Observe", b''), ("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=0, value=struct.pack('!d', Latitude_6_0_0)) + \
                                       LWM2M(id=1, value=struct.pack('!d', Longitude_6_0_1)) + \
                                       LWM2M(id=5, value=struct.pack('!L', Timestamp_6_0_5))
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                            token_buffer['/6/0'] = _token
                        # /9/0
                        elif _options_list[0] == b'' and _options_list[1] == b'9' and _options_list[2] == b'0':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Observe", b'\x0f'), ("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=8, value=intTobytes(UpdateSupportedObjects_9_0_8))  # 1代表true
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                            token_buffer['/9/0'] = _token
                        # /2053/0
                        elif _options_list[0] == b'' and _options_list[1] == b'2053' and _options_list[2] == b'0':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Observe", b'\x0f'), ("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=0, value=intTobytes(Order_2053_0_0))
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                            token_buffer['/2053/0'] = _token
                        # /3203/0
                        elif _options_list[0] == b'' and _options_list[1] == b'3203' and _options_list[2] == b'0':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Observe", b'\x0f'), ("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=5650, value=struct.pack('!d', AnalogOutputCurrentValue_3203_0_5650))
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                            token_buffer['/3203/0'] = _token
                        # /3303/0
                        elif _options_list[0] == b'' and _options_list[1] == b'3303' and _options_list[2] == b'0':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Observe", b'\x08'), ("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=5601, value=struct.pack('!d', MinMeasuredValue_3303_0_5601)) + \
                                       LWM2M(id=5602, value=struct.pack('!d', MaxMeasuredValue_3303_0_5602)) + \
                                       LWM2M(id=5700, value=struct.pack('!d', SensorValue_3303_0_5700)) + \
                                       LWM2M(id=5701, value=SensorUnits_3303_0_5701.encode())
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                            token_buffer['/3303/0'] = _token
                        # /3/0/0
                        elif _options_list[0] == b'3' and _options_list[1] == b'0' and _options_list[2] == b'0':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=0, value=Manufacturer_3_0_0.encode())
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3/0/1
                        elif _options_list[0] == b'3' and _options_list[1] == b'0' and _options_list[2] == b'1':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=1, value=ModelNumber_3_0_1.encode())
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3/0/2
                        elif _options_list[0] == b'3' and _options_list[1] == b'0' and _options_list[2] == b'2':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=2, value=SerialNumber_3_0_2.encode())
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3/0/3
                        elif _options_list[0] == b'3' and _options_list[1] == b'0' and _options_list[2] == b'3':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=3, value=FirmwareVersion_3_0_3.encode())
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3/0/9
                        elif _options_list[0] == b'3' and _options_list[1] == b'0' and _options_list[2] == b'9':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=9, value=intTobytes(BatteryLevel_3_0_9))
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3/0/10
                        elif _options_list[0] == b'3' and _options_list[1] == b'0' and _options_list[2] == b'10':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=10, value=intTobytes(MemoryFree_3_0_10))
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3/0/11
                        elif _options_list[0] == b'3' and _options_list[1] == b'0' and _options_list[2] == b'11':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(type=2, id=11,
                                             value=LWM2M(type=1, id=0, value=intTobytes(ErrorCode_3_0_11)))
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3/0/13
                        elif _options_list[0] == b'3' and _options_list[1] == b'0' and _options_list[2] == b'13':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=13, value=struct.pack('!L', CurrentTime_3_0_13))
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3/0/14
                        elif _options_list[0] == b'3' and _options_list[1] == b'0' and _options_list[2] == b'14':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=14, value=UTCOffset_3_0_14.encode())
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3/0/15
                        elif _options_list[0] == b'3' and _options_list[1] == b'0' and _options_list[2] == b'15':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=15, value=Timezone_3_0_15.encode())
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3/0/16
                        elif _options_list[0] == b'3' and _options_list[1] == b'0' and _options_list[2] == b'16':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=16, value=SupportedBindingandModes_3_0_16.encode())
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3/0/17
                        elif _options_list[0] == b'3' and _options_list[1] == b'0' and _options_list[2] == b'17':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=17, value=DeviceType_3_0_17.encode())
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3/0/18
                        elif _options_list[0] == b'3' and _options_list[1] == b'0' and _options_list[2] == b'18':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=18, value=HardwareVersion_3_0_18.encode())
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3/0/19
                        elif _options_list[0] == b'3' and _options_list[1] == b'0' and _options_list[2] == b'19':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=19, value=SoftwareVersion_3_0_19.encode())
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3/0/20
                        elif _options_list[0] == b'3' and _options_list[1] == b'0' and _options_list[2] == b'20':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=20, value=intTobytes(BatteryStatus_3_0_20))
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3/0/21
                        elif _options_list[0] == b'3' and _options_list[1] == b'0' and _options_list[2] == b'21':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=21, value=intTobytes(MemoryTotal_3_0_21))
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /6/0/0
                        elif _options_list[0] == b'6' and _options_list[1] == b'0' and _options_list[2] == b'0':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=0, value=struct.pack('!d', Latitude_6_0_0))
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /6/0/1
                        elif _options_list[0] == b'6' and _options_list[1] == b'0' and _options_list[2] == b'1':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=1, value=struct.pack('!d', Longitude_6_0_1))
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /6/0/5
                        elif _options_list[0] == b'6' and _options_list[1] == b'0' and _options_list[2] == b'5':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=5, value=struct.pack('!L', Timestamp_6_0_5))
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /9/0/8
                        elif _options_list[0] == b'9' and _options_list[1] == b'0' and _options_list[2] == b'8':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=8, value=intTobytes(UpdateSupportedObjects_9_0_8))
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /2053/0/0
                        elif _options_list[0] == b'2053' and _options_list[1] == b'0' and _options_list[2] == b'0':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=0, value=intTobytes(Order_2053_0_0))
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3203/0/5650
                        elif _options_list[0] == b'3203' and _options_list[1] == b'0' and _options_list[2] == b'5650':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=5650, value=struct.pack('!d', AnalogOutputCurrentValue_3203_0_5650))
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3303/0/5601
                        elif _options_list[0] == b'3303' and _options_list[1] == b'0' and _options_list[2] == b'5601':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=5601, value=struct.pack('!d', MinMeasuredValue_3303_0_5601))
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3303/0/5602
                        elif _options_list[0] == b'3303' and _options_list[1] == b'0' and _options_list[2] == b'5602':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=5602, value=struct.pack('!d', MaxMeasuredValue_3303_0_5602))
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3303/0/5700
                        elif _options_list[0] == b'3303' and _options_list[1] == b'0' and _options_list[2] == b'5700':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=5700, value=struct.pack('!d', SensorValue_3303_0_5700))
                            _send = _ack + _payload
                            udp_socket.sendto(_send, _addr)
                        # /3303/0/5701
                        elif _options_list[0] == b'3303' and _options_list[1] == b'0' and _options_list[2] == b'5701':
                            _ack = bytes(CoAP(type="ACK",
                                              code="2.05 Content",
                                              msg_id=_msg_id,
                                              token=_token,
                                              options=[("Content-Format", b'\x2d\x16')],
                                              paymark=b'\xff'))
                            _payload = LWM2M(id=5701, value=SensorUnits_3303_0_5701.encode())
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
                        udp_socket.sendto(_send, _addr)

                # 收到ACK应答
                elif _type == 2:
                    # code为2.01 Created
                    if _code == 65:
                        print(color.yellow('收到上线回应'))
