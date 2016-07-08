# p2psp-experiments

This repository is aimed at experimenting certain things with the P2PSP protocol.
Currently, the experiment is to run splitters in parallel that transmit the same video stream. The objective is to take advantage of this parallelization among the peers so that latency may be reduced.

## STATUS
Synchronizer ***partially*** complete

~~Synchronize function is now complete.~~

WIP on mixing various streams.

## TODO
**Use mutexes wherever there is concurrent I/O**

~~Create a new entity called Synchronizer that takes multiple streams from the peer and synchronizes them into one single stream and then feeds the player.~~

~~Develop Synchronizer.~~

Complete the remaining functionality

### Last updated : 08 July, 2016 23:50:32 UTC+0530
