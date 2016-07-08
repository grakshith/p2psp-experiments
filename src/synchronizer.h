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
#include <arpa/inet.h>
#include <boost/array.hpp>
#include <boost/asio.hpp>
#include <boost/date_time/posix_time/posix_time.hpp>
#include <boost/thread/thread.hpp>
#include <ctime>
#include <fstream>
#include <string>
#include <tuple>
#include <vector>
#include <boost/algorithm/string.hpp>
#include <boost/lexical_cast.hpp>

namespace p2psp {

class Synchronizer {
public:
    Synchronizer();
    ~Synchronizer();

    const std::vector<std::string>* peer_list;                        //Vector which holds the addresses of peers
    std::vector<std::vector<char> > peer_data;                        //Vector to hold the chunk data of each peer
    boost::thread_group thread_group_;                                //Thread group manages the peer threads
    boost::asio::io_service io_service_;                               // Service for I/O operations
    boost::asio::ip::tcp::acceptor acceptor_;                          // Acceptor used to listen to incoming connections.
    boost::asio::ip::tcp::socket player_socket_;                       // Socket to send chunks to player
    unsigned short player_port;                                                 // Player Port

    void Run(int argc, const char* argv[]) throw(boost::system::system_error);  //Run the argument parser
    void PlayChunk();  //Play the chunk to the player
    void Synchronize(); //To get the offset from the first peer and synchronize the lists
    void ConnectToPeers(std::string,int) throw(boost::system::system_error); //Connect the synchronizer with various peers
    void RunThreads(); //To run the threads to connect to peers
    void MixStreams(); //To construct a vector by mixing chunks from peer_data vector
    };
}
