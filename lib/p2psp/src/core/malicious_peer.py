"""
@package core
malicious_peer module
"""

# -*- coding: iso-8859-15 -*-

# This code is distributed under the GNU General Public License (see
# THE_GENERAL_GNU_PUBLIC_LICENSE.txt for extending this information).
# Copyright (C) 2015, the P2PSP team.
# http://www.p2psp.org

import struct
import socket
import sys
import threading
import random

from core.color import Color
from core._print_ import _print_
from core.peer_dbs import Peer_DBS

def _p_(*args, **kwargs):
    """Colorize the output."""
    sys.stdout.write(Common.DBS)
    _print_("DBS (malicious):", *args)
    sys.stdout.write(Color.none)

class MaliciousPeer(Peer_DBS):

    persistentAttack = False
    onOffAttack = False
    onOffRatio = 100
    selectiveAttack = False
    selectedPeersForAttack = []

    def __init__(self, peer):
        # {{{

        _p_("Initialized")
        
        # }}}

    def process_message(self, message, sender):
        # {{{ Now, receive and send.

        if len(message) == struct.calcsize(self.message_format):
            # {{{ A video chunk has been received

            chunk_number, chunk = self.unpack_message(message)
            self.chunks[chunk_number % self.buffer_size] = chunk
            self.received_flag[chunk_number % self.buffer_size] = True
            self.received_counter += 1

            if sender == self.splitter:
                # {{{ Send the previous chunk in burst sending
                # mode if the chunk has not been sent to all
                # the peers of the list of peers.

                # {{{ debug

                if __debug__:
                    _print_("DBS:", self.team_socket.getsockname(), \
                        Color.red, "<-", Color.none, chunk_number, "-", sender)

                # }}}

                while( (self.receive_and_feed_counter < len(self.peer_list)) and (self.receive_and_feed_counter > 0) ):
                    peer = self.peer_list[self.receive_and_feed_counter]
                    self.send_chunk(peer)

                    # {{{ debug

                    if __debug__:
                        print ("DBS:", self.team_socket.getsockname(), "-",\
                            socket.ntohs(struct.unpack(self.message_format, \
                                                           self.receive_and_feed_previous)[0]),\
                            Color.green, "->", Color.none, peer)

                    # }}}

                    self.debt[peer] += 1
                    if self.debt[peer] > self.MAX_CHUNK_DEBT:
                        print (Color.red, "DBS:", peer, 'removed by unsupportive (' + str(self.debt[peer]) + ' lossess)', Color.none)
                        del self.debt[peer]
                        self.peer_list.remove(peer)

                    self.receive_and_feed_counter += 1

                self.receive_and_feed_counter = 0
                self.receive_and_feed_previous = message

               # }}}
            else:
                # {{{ The sender is a peer

                # {{{ debug

                if __debug__:
                    print ("DBS:", self.team_socket.getsockname(), \
                        Color.green, "<-", Color.none, chunk_number, "-", sender)

                # }}}

                if sender not in self.peer_list:
                    # The peer is new
                    self.peer_list.append(sender)
                    self.debt[sender] = 0
                    print (Color.green, "DBS:", sender, 'added by chunk', \
                        chunk_number, Color.none)
                else:
                    self.debt[sender] -= 1

                # }}}

            # {{{ A new chunk has arrived and the
            # previous must be forwarded to next peer of the
            # list of peers.
            if ( self.receive_and_feed_counter < len(self.peer_list) and ( self.receive_and_feed_previous != '') ):
                # {{{ Send the previous chunk in congestion avoiding mode.

                peer = self.peer_list[self.receive_and_feed_counter]
                self.send_chunk(peer)

                self.debt[peer] += 1
                if self.debt[peer] > self.MAX_CHUNK_DEBT:
                    print (Color.red, "DBS:", peer, 'removed by unsupportive (' + str(self.debt[peer]) + ' lossess)', Color.none)
                    del self.debt[peer]
                    self.peer_list.remove(peer)

                # {{{ debug

                if __debug__:
                    print ("DBS:", self.team_socket.getsockname(), "-", \
                        socket.ntohs(struct.unpack(self.message_format, self.receive_and_feed_previous)[0]),\
                        Color.green, "->", Color.none, peer)

                # }}}

                self.receive_and_feed_counter += 1

                # }}}
            # }}}

            return chunk_number

            # }}}
        else:
            # {{{ A control chunk has been received
            print("DBS: Control received")
            if message == 'H':
                if sender not in self.peer_list:
                    # The peer is new
                    self.peer_list.append(sender)
                    self.debt[sender] = 0
                    print (Color.green, "DBS:", sender, 'added by [hello]', Color.none)
            else:
                if sender in self.peer_list:
                    sys.stdout.write(Color.red)
                    print ("DBS:", self.team_socket.getsockname(), '\b: received "goodbye" from', sender)
                    sys.stdout.write(Color.none)
                    self.peer_list.remove(sender)
                    del self.debt[sender]
            return -1

            # }}}

        # }}}

    def send_chunk(self, peer):
        if self.persistentAttack:
            self.team_socket.sendto(self.get_poisoned_chunk(self.receive_and_feed_previous), peer)
            self.sendto_counter += 1
            return

        if self.onOffAttack:
            r = random.randint(1, 100)
            if r <= self.onOffRatio:
                self.team_socket.sendto(self.get_poisoned_chunk(self.receive_and_feed_previous), peer)
            else:
                self.team_socket.sendto(self.receive_and_feed_previous, peer)

            self.sendto_counter += 1
            return

        if self.selectiveAttack:
            if peer in self.selectedPeersForAttack:
                self.team_socket.sendto(self.get_poisoned_chunk(self.receive_and_feed_previous), peer)
            else:
                self.team_socket.sendto(self.receive_and_feed_previous, peer)

            self.sendto_counter += 1
            return

        self.team_socket.sendto(self.receive_and_feed_previous, peer)
        self.sendto_counter += 1

    def get_poisoned_chunk(self, chunk):
        chunk_number, chunk = struct.unpack(self.message_format, chunk)
        return struct.pack(self.message_format, chunk_number, '0')

    def setPersistentAttack(self, value):
        self.persistentAttack = value

    def setOnOffAttack(self, value, ratio):
        self.onOffAttack = True
        self.onOffRatio = ratio

    def setSelectiveAttack(self, value, selected):
        self.selectiveAttack = True
        for peer in selected:
            l = peer.split(':')
            peer_obj = (l[0], int(l[1]))
            self.selectedPeersForAttack.append(peer_obj)
