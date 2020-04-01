from scapy.fields import *
from scapy.packet import *

_Control_Packet_Type = ({
                            1: "CONNECT",  # 客户端―→服务端       客户端请求连接到服务端的代理服务
                            2: "CONNACK",  # 客户端←―服务端       连接请求的回复确认报文
                            3: "PUBLISH",  # 客户端←→服务端       发布主题消息
                            4: "PUBACK",  # 客户端←→服务端        发布确认，是QoS=1时，对 PUBLISH 的响应确认
                            5: "PUBREC",  # 客户端←→服务端        发布收到，是QoS=2时，对 PUBLISH 的响应确认，是QoS=2实现的第一步
                            6: "PUBREL",  # 客户端←→服务端        发布释放，是QoS=2时，对 PUBREC 的响应确认，是QoS=2实现的第二步
                            7: "PUBCOMP",  # 客户端←→服务端       发布完成，是QoS=2时，对 PUBREL 的响应确认，是QoS=2实现的第三步
                            8: "SUBSCRIBE",  # 客户端―→服务端     客户端订阅主题，可一次订阅一个或多个主题（使用通配符）
                            9: "SUBACK",  # 客户端←―服务端        订阅完成确认，是对 SUBSCRIBE 的响应确认
                            10: "UNSUBSCRIBE",  # 客户端―→服务端  取消订阅，客户端发起的取消对某个主题的订阅
                            11: "UNSUBACK",  # 客户端←―服务端     取消订阅确认，是对 UNSUBSCRIBE 的响应确认
                            12: "PINGREQ",  # 客户端―→服务端      心跳，表示这个数据包是为通知服务端客户端还在正常连接着
                            13: "PINGRESP",  # 客户端←―服务端     心跳响应，表示服务端已经成功收到了客户端的心跳
                            14: "DISCONNECT"  # 客户端―→服务端    断开连接，客户端通知服务端，需要断开当前网络连接
                        },
                        {
                            "CONNECT": 1,  # 客户端―→服务端       客户端请求连接到服务端的代理服务
                            "CONNACK": 2,  # 客户端←―服务端       连接请求的回复确认报文
                            "PUBLISH": 3,  # 客户端←→服务端       发布主题消息
                            "PUBACK": 4,  # 客户端←→服务端        发布确认，是QoS=1时，对 PUBLISH 的响应确认
                            "PUBREC": 5,  # 客户端←→服务端        发布收到，是QoS=2时，对 PUBLISH 的响应确认，是QoS=2实现的第一步
                            "PUBREL": 6,  # 客户端←→服务端        发布释放，是QoS=2时，对 PUBREC 的响应确认，是QoS=2实现的第二步
                            "PUBCOMP": 7,  # 客户端←→服务端       发布完成，是QoS=2时，对 PUBREL 的响应确认，是QoS=2实现的第三步
                            "SUBSCRIBE": 8,  # 客户端―→服务端     客户端订阅主题，可一次订阅一个或多个主题（使用通配符）
                            "SUBACK": 9,  # 客户端←―服务端        订阅完成确认，是对 SUBSCRIBE 的响应确认
                            "UNSUBSCRIBE": 10,  # 客户端―→服务端  取消订阅，客户端发起的取消对某个主题的订阅
                            "UNSUBACK": 11,  # 客户端←―服务端     取消订阅确认，是对 UNSUBSCRIBE 的响应确认
                            "PINGREQ": 12,  # 客户端―→服务端      心跳，表示这个数据包是为通知服务端客户端还在正常连接着
                            "PINGRESP": 13,  # 客户端←―服务端     心跳响应，表示服务端已经成功收到了客户端的心跳
                            "DISCONNECT": 14  # 客户端―→服务端    断开连接，客户端通知服务端，需要断开当前网络连接
                        })


# MQTT固定报头
class MQTT_Fixed_Header(Packet):
    __slots__ = ["content_format"]
    name = "MQTT Fixed Header"
    fields_desc = [BitEnumField("control_packet_type", 1, 4, _Control_Packet_Type),
                   BitField("dup", 0, 1),  # 是否为重复发
                   BitField("qos_high", 0, 1),  # 服务质量高位
                   BitField("qos_low", 0, 1),  # 服务质量低位
                   BitField("retain", 0, 1)  # 是否保存消息
                   ]
