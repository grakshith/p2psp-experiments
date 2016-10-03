# p2psp-experiments

This repository is aimed at experimenting certain things with the P2PSP protocol.
Currently, the experiment is to run splitters in parallel that transmit the same video stream. The objective is to take advantage of this parallelization among the peers so that latency may be reduced and the protocol be made more error resilient.

## STATUS
Synchronizer merged with upstream **[here]** (https://github.com/hehaichi/p2psp-console/blob/master/src/synchronizer.cc).

Only MPEG4-TS works as of now

~~VLC dropping frames~~

~~Synchronize function is now complete.~~

~~WIP on mixing various streams.~~

~~Working on the headers for the synchronized output~~

## TODO
Extend synchronizer for all video formats

~~**Use mutexes wherever there is concurrent I/O**~~

~~Create a new entity called Synchronizer that takes multiple streams from the peer and synchronizes them into one single stream and then feeds the player.~~

~~Develop Synchronizer.~~

~~Complete the remaining functionality~~

~~In the current implementation, although a ```set``` data structure is employed, there is a possibility of a duplicate chunk being added to the set. This happens when there is a delay between two synchronized peers. This happens because, as soon as the synchronized chunk is played, it is removed from the set.~~

* ~~Define buffer size for the vector and use it like a circular queue~~

* ~~Make the output playable by VLC~~


### Last updated : 3 October, 2016 21:50:45 UTC+0530
