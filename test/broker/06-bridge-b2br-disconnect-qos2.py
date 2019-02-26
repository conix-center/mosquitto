#!/usr/bin/env python

# Does a bridge resend a QoS=1 message correctly after a disconnect?

from mosq_test_helper import *

def write_config(filename, port1, port2):
    with open(filename, 'w') as f:
        f.write("port %d\n" % (port2))
        f.write("\n")
        f.write("connection bridge_sample\n")
        f.write("address 127.0.0.1:%d\n" % (port1))
        f.write("topic bridge/# both 2\n")
        f.write("notifications false\n")
        f.write("restart_timeout 5\n")

(port1, port2) = mosq_test.get_port(2)
conf_file = os.path.basename(__file__).replace('.py', '.conf')
write_config(conf_file, port1, port2)

rc = 1
keepalive = 60
client_id = socket.gethostname()+".bridge_sample"
connect_packet = mosq_test.gen_connect(client_id, keepalive=keepalive, clean_session=False, proto_ver=128+4)
connack_packet = mosq_test.gen_connack(rc=0)

mid = 1
subscribe_packet = mosq_test.gen_subscribe(mid, "bridge/#", 2)
suback_packet = mosq_test.gen_suback(mid, 2)

mid = 2
subscribe2_packet = mosq_test.gen_subscribe(mid, "bridge/#", 2)
suback2_packet = mosq_test.gen_suback(mid, 2)

mid = 3
subscribe3_packet = mosq_test.gen_subscribe(mid, "bridge/#", 2)
suback3_packet = mosq_test.gen_suback(mid, 2)

mid = 5
publish_packet = mosq_test.gen_publish("bridge/disconnect/test", qos=2, mid=mid, payload="disconnect-message")
publish_dup_packet = mosq_test.gen_publish("bridge/disconnect/test", qos=2, mid=mid, payload="disconnect-message", dup=True)
pubrec_packet = mosq_test.gen_pubrec(mid)
pubrel_packet = mosq_test.gen_pubrel(mid)
pubcomp_packet = mosq_test.gen_pubcomp(mid)

ssock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ssock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
ssock.settimeout(40)
ssock.bind(('', port1))
ssock.listen(5)

broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port2, use_conf=True)

try:
    (bridge, address) = ssock.accept()
    bridge.settimeout(20)

    if mosq_test.expect_packet(bridge, "connect", connect_packet):
        bridge.send(connack_packet)

        if mosq_test.expect_packet(bridge, "subscribe", subscribe_packet):
            bridge.send(suback_packet)

            bridge.send(publish_packet)
            bridge.close()

            (bridge, address) = ssock.accept()
            bridge.settimeout(20)

            if mosq_test.expect_packet(bridge, "connect", connect_packet):
                bridge.send(connack_packet)

                if mosq_test.expect_packet(bridge, "2nd subscribe", subscribe2_packet):
                    bridge.send(suback2_packet)
                    bridge.send(publish_dup_packet)

                    if mosq_test.expect_packet(bridge, "pubrec", pubrec_packet):
                        bridge.send(pubrel_packet)
                        bridge.close()

                        (bridge, address) = ssock.accept()
                        bridge.settimeout(20)

                        if mosq_test.expect_packet(bridge, "connect", connect_packet):
                            bridge.send(connack_packet)

                            if mosq_test.expect_packet(bridge, "3rd subscribe", subscribe3_packet):
                                bridge.send(suback3_packet)

                                bridge.send(publish_dup_packet)

                                if mosq_test.expect_packet(bridge, "2nd pubrec", pubrec_packet):
                                    bridge.send(pubrel_packet)

                                    if mosq_test.expect_packet(bridge, "pubcomp", pubcomp_packet):
                                        rc = 0

    bridge.close()
finally:
    os.remove(conf_file)
    try:
        bridge.close()
    except NameError:
        pass

    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde)
    ssock.close()

exit(rc)

