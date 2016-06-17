#! /bin/sh
./../bin/splitter --NTS --source_addr 150.214.150.68 --source_port 4551 --channel BBB-134.ogv > /dev/null &
sleep 5
./../bin/splitter --NTS --source_addr 150.214.150.68 --source_port 4551 --team_port 8002 --channel BBB-134.ogv > /dev/null &
./../bin/peer --monitor --splitter_addr 127.0.0.1 --splitter_port 8001 > /dev/null &
sleep 3
./../bin/peer --monitor --splitter_addr 127.0.0.1 --splitter_port 8002 --player_port 10000 > /dev/null &
vlcold http://localhost:9999 &
sleep 3
vlcold http://localhost:10000 &
