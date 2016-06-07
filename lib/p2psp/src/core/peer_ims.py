"""
@package core
peer_ims module
"""

# -*- coding: iso-8859-15 -*-

# This code is distributed under the GNU General Public License (see
# THE_GENERAL_GNU_PUBLIC_LICENSE.txt for extending this information).
# Copyright (C) 2014, the P2PSP team.
# http://www.p2psp.org

# IMS: Ip Multicasting Set of rules

# {{{ Imports

from __future__ import print_function
import threading
import sys
import socket
import struct
import time

from core.common import Common

from core._print_ import _print_
from core.color import Color

#from gi.repository import GObject
try:
    from gui.adapter import buffering_adapter
except ImportError as msg:
    pass

# }}}

def _p_(*args, **kwargs):
    """Colorize the output."""
    if __debug__:
        sys.stdout.write(Common.IMS_COLOR)
        _print_("IMS:", *args)
        sys.stdout.write(Color.none)

class Peer_IMS(threading.Thread):
    # {{{

    # {{{ Class "constants"

    PLAYER_PORT = 9999          # Port used to serve the player.
    SPLITTER_ADDR = "127.0.0.1" # Address of the splitter.
    SPLITTER_PORT = 8001        # Port of the splitter.
    PORT = 0                    # TCP->UDP port used to communicate.
    USE_LOCALHOST = False       # Use localhost instead the IP of the addapter
    BUFFER_STATUS = int(0)      # ?
    SHOW_BUFFER = False

    # }}}

    def __new__(new_type, *args, **kwargs):
        # {{{

        if len(args) == 1 and isinstance(args[0], Peer_IMS):
            # Parameter is a peer instance; extending its class instead of nesting:
            instance = args[0]
            old_type = instance.__class__
            new_class_name = old_type.__name__ + '.' + new_type.__name__
            instance.__class__ = type(new_class_name, (old_type,), dict(new_type.__dict__))
            return instance
        else:
            # Use default object creation
            return object.__new__(new_type, *args, **kwargs)

        # }}}

    def __init__(self):
        # {{{
        threading.Thread.__init__(self)

        _p_("Player port =", self.PLAYER_PORT)
        _p_("Splitter =", self.SPLITTER_ADDR)
        _p_("(Peer) port =", self.PORT)
        _p_("Initialized")

        # }}}

    def wait_for_the_player(self):
        # {{{ Setup "player_socket" and wait for the player

        self.player_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # In Windows systems this call doesn't work!
            self.player_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception as e:
            _p_(e)
            pass
        self.player_socket.bind(('', self.PLAYER_PORT))
        self.player_socket.listen(0)
        _p_("Waiting for the player at", self.player_socket.getsockname())
        self.player_socket = self.player_socket.accept()[0]
        #self.player_socket.setblocking(0)
        _p_("The player is", self.player_socket.getpeername())

        # }}}

    def connect_to_the_splitter(self):
        # {{{ Setup "splitter" and "splitter_socket"

        # Nota: Ahora no reconvertimos de TCP a UDP!

        self.splitter_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.splitter = (self.SPLITTER_ADDR, self.SPLITTER_PORT)
        _p_("use_localhost =", self.USE_LOCALHOST)
        if self.USE_LOCALHOST:
            my_ip = '0.0.0.0' # Or '127.0.0.1'
            #my_ip = '127.0.0.1'
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(self.splitter)
            #my_ip = socket.gethostbyname(socket.gethostname())
            my_ip = s.getsockname()[0]
            s.close()
        _p_("Connecting to the splitter at", self.splitter, "from", my_ip)
        if self.PORT != 0:
            try:
                self.splitter_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except Exception as e:
                _print_(e)
                pass
            #sys.stdout.write(Color.purple)
            _p_("I'm using port the port", self.PORT)
            #sys.stdout.write(Color.none)
            self.splitter_socket.bind((my_ip, self.PORT))
        else:
            self.splitter_socket.bind((my_ip, 0))
        try:
            self.splitter_socket.connect(self.splitter)
        except Exception as e:
            if __debug__:
                _p_(e)
            else:
                _print_(e)
            #sys.stdout.write(Color.red)
            #sys.exit("Sorry. Can't connect to the splitter at " + str(self.splitter))
            #sys.stdout.write(Color.none)
            sys.exit()
        _p_("Connected to the splitter at", self.splitter)

        # }}}

    def disconnect_from_the_splitter(self):
        # {{{

        self.splitter_socket.close()

        # }}}

    def receive_the_mcast_endpoint(self):
        # {{{
        message = self.splitter_socket.recv(struct.calcsize("4sH"))
        addr, port = struct.unpack("4sH", message)
        self.mcast_addr = socket.inet_ntoa(addr)
        self.mcast_port = socket.ntohs(port)
        mcast_endpoint = (self.mcast_addr, self.mcast_port)
        _p_("mcast_endpoint =", mcast_endpoint)

        # }}}

    def receive_the_header(self):
        # {{{

        header_size_in_bytes = self.header_size_in_chunks * self.chunk_size
        received = 0
        data = ""
        while received < header_size_in_bytes:
            data = self.splitter_socket.recv(header_size_in_bytes - received)
            received += len(data)
            _p_("Percentage of header received = {:.2%}".format((1.0*received)/header_size_in_bytes))
            try:
                self.player_socket.sendall(data)
            except Exception as e:
                _p_(e)
                _p_("error sending data to the player")
                _p_("len(data) =", len(data))
                time.sleep(1)
            _p_("received bytes:", received, "\r", end="")

        _p_("Received", received, "bytes of header")

        # }}}

    def receive_the_chunk_size(self):
        # {{{

        # The size of the chunk in bytes.
        message = self.splitter_socket.recv(struct.calcsize("H"))
        chunk_size = struct.unpack("H", message)[0]
        self.chunk_size = socket.ntohs(chunk_size)
        _p_("chunk_size (bytes) =", self.chunk_size)
        self.message_format = "H" + str(self.chunk_size) + "s"
        _p_("message_format = ", self.message_format)

        # }}}

    def receive_the_header_size(self):
        # {{{

        message = self.splitter_socket.recv(struct.calcsize("H"))
        value = struct.unpack("H", message)[0]
        self.header_size_in_chunks = socket.ntohs(value)
        _p_("header_size (in chunks) =", self.header_size_in_chunks)

        # }}}

    def receive_the_buffer_size(self):
        # {{{

        message = self.splitter_socket.recv(struct.calcsize("H"))
        buffer_size = struct.unpack("H", message)[0]
        self.buffer_size = socket.ntohs(buffer_size)
        _p_("buffer_size =", self.buffer_size)

        # }}}

    def create_team_socket(self):
        # {{{ Create "team_socket" (UDP) for using the multicast channel

        # This method can be overridden to use special socket types
        self.team_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        # }}}

    def listen_to_the_team(self):
        # {{{ Create "team_socket" (UDP) for using the multicast channel

        self.create_team_socket()
        try:
            self.team_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception as e:
            _p_(e)
            pass

        try:
            self.team_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except Exception as e:
            _p_(e)
            pass

        self.team_socket.bind(('', self.mcast_port))
#        self.team_socket.bind(('', self.SPLITTER_SOCKET.getsockname()[PORT]))

        mreq = struct.pack("4sl", socket.inet_aton(self.mcast_addr), socket.INADDR_ANY)
        self.team_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        _p_("Listening to the mcast_channel =", (self.mcast_addr, self.mcast_port))

        # This is the maximum time the peer will wait for a chunk
        # (from the splitter).
        self.team_socket.settimeout(1)
        _p_(self.team_socket.getsockname(), "\b.timeout = 1")

        # }}}

    def unpack_message(self, message):
        # {{{

        chunk_number, chunk = struct.unpack(self.message_format, message)
        chunk_number = socket.ntohs(chunk_number)

        return chunk_number, chunk

        # }}}

    def receive_the_next_message(self):
        # {{{

        _p_("Waiting for a chunk at {} ...".format(self.team_socket.getsockname()))

        message, sender = self.team_socket.recvfrom(struct.calcsize(self.message_format))
        self.recvfrom_counter += 1

        _p_("Received a message from", sender, "of length", len(message))
        if __debug__:
            if len(message) < 10:
                _p_("Message content =", message)

        return message, sender

        # }}}

    # This method is overridden by the inheriting classes DBS and NTS
    def process_message(self, message, sender):
        # {{{

        # Ojo, an attacker could send a packet smaller and pollute the
        # buffer, althought this is difficult in IP multicst. This
        # method should be inheritaged to solve this issue.

        chunk_number, chunk = self.unpack_message(message)

        self.chunks[chunk_number % self.buffer_size] = chunk
        self.received_flag[chunk_number % self.buffer_size] = True
        self.received_counter += 1

        return chunk_number

        # }}}

    def process_next_message(self):
        # {{{
        try:
            message, sender = self.receive_the_next_message()
        except socket.timeout:
            return -2

        return self.process_message(message, sender)

        #except Exception:
        #    return -1

        # }}}

    def buffer_data(self):
        # {{{ Buffering

        # {{{ The peer dies if the player disconnects.
        # }}}
        self.player_alive = True

        # {{{ The last chunk sent to the player.
        # }}}
        self.played_chunk = 0

        # {{{ Counts the number of executions of the recvfrom()
        # function.
        # }}}
        self.recvfrom_counter = 0

        # {{{ Label the chunks in the buffer as "received" or "not
        # received".
        # }}}
        self.received_flag = []

        # {{{ The buffer of chunks is a structure that is used to delay
        # the playback of the chunks in order to accommodate the
        # network jittter. Two components are needed: (1) the "chunks"
        # buffer that stores the received chunks and (2) the
        # "received" buffer that stores if a chunk has been received
        # or not. Notice that each peer can use a different
        # buffer_size: the smaller the buffer size, the lower start-up
        # time, the higher chunk-loss ratio. However, for the sake of
        # simpliticy, all peers will use the same buffer size.

        self.chunks = [""]*self.buffer_size
        self.received_flag = [False]*self.buffer_size
        self.received_counter = 0

        # }}}

        #  Wall time (execution time plus waiting time).
        start_time = time.time()

        # We will send a chunk to the player when a new chunk is
        # received. Besides, those slots in the buffer that have not been
        # filled by a new chunk will not be send to the player. Moreover,
        # chunks can be delayed an unknown time. This means that (due to the
        # jitter) after chunk X, the chunk X+Y can be received (instead of the
        # chunk X+1). Alike, the chunk X-Y could follow the chunk X. Because
        # we implement the buffer as a circular queue, in order to minimize
        # the probability of a delayed chunk overwrites a new chunk that is
        # waiting for traveling the player, we wil fill only the half of the
        # circular queue.

        _p_(self.team_socket.getsockname(), "\b: buffering = 000.00%")
        sys.stdout.flush()

        # First chunk to be sent to the player.  The
        # process_next_message() procedure returns the chunk number if
        # a packet has been received or -2 if a time-out exception has
        # been arised.
        chunk_number = self.process_next_message()
        while chunk_number < 0:
            chunk_number = self.process_next_message()
            _p_(chunk_number)
        self.played_chunk = chunk_number
        _p_("First chunk to play", self.played_chunk)
        _p_(self.team_socket.getsockname(), "\b: buffering (\b", repr(100.0/self.buffer_size).rjust(4))

        # Now, fill up to the half of the buffer.
        for x in range(int(self.buffer_size/2)):
            _print_("{:.2%}\r".format((1.0*x)/(self.buffer_size/2)), end='')
            BUFFER_STATUS = (100*x)/(self.buffer_size/2) +1
            #if Common.CONSOLE_MODE == False :
            #    GObject.idle_add(buffering_adapter.update_widget,BUFFER_STATUS)
            #else:
            #    pass
            #print("!", end='')
            sys.stdout.flush()
            while self.process_next_message() < 0:
                pass

        print()
        latency = time.time() - start_time
        _p_('latency =', latency, 'seconds')
        _p_("buffering done.")
        sys.stdout.flush()

        # }}}

    # Tiene pinta de que los tres siguientes metodos pueden
    # simplificarse...

    def find_next_chunk(self):
        # {{{
        #print (".")
        #counter = 0
        chunk_number = (self.played_chunk + 1) % Common.MAX_CHUNK_NUMBER
        while not self.received_flag[chunk_number % self.buffer_size]:
            #sys.stdout.write(Color.cyan)
            _p_("lost chunk", chunk_number)
            #sys.stdout.write(Color.none)
            chunk_number = (chunk_number + 1) % Common.MAX_CHUNK_NUMBER
            #counter += 1
            #if counter > self.buffer_size:
            #    break
        return chunk_number

        # }}}

    def play_chunk(self, chunk):
        # {{{

        try:
            self.player_socket.sendall(self.chunks[chunk % self.buffer_size])
        except socket.error:
            #print(e)
            _p_("Player disconnected!")
            self.player_alive = False

        # }}}

    def play_next_chunk(self):
        # {{{

        self.played_chunk = self.find_next_chunk()
        self.play_chunk(self.played_chunk)
        self.received_flag[self.played_chunk % self.buffer_size] = False
        self.received_counter -= 1
        #print("----------------------------")

        # }}}

    def play(self):
        # {{{

        while self.player_alive:
            #self.keep_the_buffer_full()
            self.play_next_chunk()

        # }}}

    ## def receive_configuration(self):
    ##     # {{{

    ##     self.receive_the_mcast_endpoint()
    ##     self.receive_the_header_size()
    ##     self.receive_the_chunk_size()
    ##     self.receive_the_header()
    ##     self.receive_the_buffer_size()

    ##     # }}}

    def keep_the_buffer_full(self):
        # {{{

        # Receive chunks while the buffer is not full
        #while True:
        #    chunk_number = self.process_next_message()
        #    if chunk_number >= 0:
        #        break
        chunk_number = self.process_next_message()
        current_time=time.time()
        while chunk_number < 0:
            chunk_number = self.process_next_message()
            if((time.time()-current_time)>15):
                return -2
        #while ((chunk_number - self.played_chunk) % self.buffer_size) < self.buffer_size/2:
        while self.received_counter < self.buffer_size/2:
            chunk_number = self.process_next_message()
            while chunk_number < 0:
                chunk_number = self.process_next_message()

        if self.SHOW_BUFFER:
            for i in range(self.buffer_size):
                if self.received_flag[i]:
                    sys.stdout.write(str(i%10))
                else:
                    sys.stdout.write('.')
            print ()
            #print (self.team_socket.getsockname(),)
            #sys.stdout.write(Color.none)

        # }}}

    def run(self):
        # {{{

        #threading.Thread(target=self.play).start()

        while self.player_alive:
            status=self.keep_the_buffer_full()
            self.play_next_chunk()
            if(status==-2):
                return

        # }}}

    # }}}
