//
//  synchronizer.h
//  P2PSP
//
//  This code is distributed under the GNU General Public License (see
//  THE_GENERAL_GNU_PUBLIC_LICENSE.txt for extending this information).
//  Copyright (C) 2016, the P2PSP team.
//  http://www.p2psp.org
//

#include <boost/format.hpp>
#include <boost/program_options/parsers.hpp>
#include <boost/program_options/variables_map.hpp>
#include "../lib/p2psp/src/util/trace.h"

namespace p2psp {

class Synchronizer {
public:
    Synchronizer();
    ~Synchronizer();
    
    void Run();  //Run the argument parser
    void PlayChunk();  //Play the chunk to the player
    void Synchronize(); //To get the offset from the first peer and synchronize the lists
    void ConnectToPeers(); //Connect the synchronizer with various peers
    };
}
    

