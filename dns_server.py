#!/home/nightwish/nipple/intercept_dns/env/bin/python2.7
# coding: utf8

"""
一个干净的DNS
"""

from argparse import ArgumentParser
import socket
from SocketServer import ThreadingUDPServer, DatagramRequestHandler
# from threading import Thread

from dnslib import DNSRecord, DNSQuestion, RR


class CleanDNSHandler(DatagramRequestHandler):

    def __init__(self, request, client_address, server):
        self.request = request
        self.client_address = client_address
        self.server = server
        self.setup()
        try:
            self.handle()
        except StandardError, error_message:
            log.exception(error_message)
        else:
            self.finish()

    def parse(self):
        query_parse_ret = DNSRecord.parse(self.packet)
        self.query_id = query_parse_ret.header.id
        self.qname = str(query_parse_ret.q.qname).strip(".")
        self.qtype = query_parse_ret.q.qtype

    def manufactory_DNS(self):
        response_packet = DNSRecord()
        response_packet.header.id = self.query_id
        response_packet.add_question(DNSQuestion(self.qname, self.qtype))
        related_rr = filter(lambda rr: self.qname in rr, intercept_rr)
        for answer in related_rr:
            response_packet.add_answer(*RR.fromZone(answer))
        self.response_packet = response_packet.pack().__str__()

    def request_upstream_DNS(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect((args.upstream, 53))
        sock.send(self.packet)
        self.response_packet = sock.recv(1024)

    def handle(self):
        """
        处理DNS请求的主体流程
        """
        # 请求包解析
        self.parse()

        if self.qname in intercept_domain:
            # 动手制作DNS响应包
            self.manufactory_DNS()
        else:
            # 请求上游DNS
            self.request_upstream_DNS()

        log.info(
            "client_ip: {} qname: {} qtype: {}".format(
                self.client_address[0], self.qname, self.qtype,
            )
        )

    def finish(self):
        self.socket.sendto(self.response_packet, self.client_address)
        for answer in DNSRecord.parse(self.response_packet).rr:
            log.info(
                "client_ip: {} rname: {} rtype: {} rdata: {}".format(
                    self.client_address[0],
                    str(answer.rname).strip("."), answer.rtype, answer.rdata,
                )
            )

if __name__ == "__main__":
    parser = ArgumentParser(
        description="dns proxy",
        epilog="enjoy it!",
    )
    parser.add_argument(
        "-a", "--host",
        type=str, default="0.0.0.0",
        help="the host you want to listen",
    )
    parser.add_argument(
        "-p", "--port",
        type=int, default=53,
        help="the port your want to listen",
    )
    parser.add_argument(
        "-i", "--intercept",
        type=str, default="",
        help="the glob file with  domain your want to set",
    )
    parser.add_argument(
        "--logfile",
        type=str, default="",
        help="which log file you want to output",
    )
    parser.add_argument(
        "--upstream",
        type=str, default="8.8.8.8",
        help="upstream DNS",
    )
    args = parser.parse_args()

    from logging import StreamHandler
    from logging.handlers import TimedRotatingFileHandler
    stream_handler = StreamHandler()
    file_handler = TimedRotatingFileHandler(
        args.logfile, when="D", interval=1, delay=True,
    )

    from logging import Formatter
    formatter = Formatter(
        fmt='%(asctime)s %(message)s',
        datefmt='%Y-%m-%d--%H:%M:%S',
    )
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    from logging import getLogger
    log = getLogger(__name__)
    log.addHandler(file_handler)
    # log.addHandler(stream_handler)
    # fuck = getLogger("{}_stream_logger".format(__name__))
    # fuck.addHandler(stream_handler)

    from logging import INFO
    log.setLevel(INFO)
    # fuck.setLevel(INFO)

    intercept_domain, intercept_rr = [], []
    with open(args.intercept) as zonefile:
        for zone in zonefile:
            intercept_domain.append(zone.split(" ")[0])
            intercept_rr.append(zone)
    intercept_domain = list(set(intercept_domain))

    server = ThreadingUDPServer((args.host, args.port), CleanDNSHandler)
    # server_thread = Thread(target=server.serve_forever)
    # server_thread.daemon = False
    try:
        # server_thread.start()
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        server.server_close()
