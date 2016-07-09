//
//  synchronizer.cc
//  P2PSP
//
//  This code is distributed under the GNU General Public License (see
//  THE_GENERAL_GNU_PUBLIC_LICENSE.txt for extending this information).
//  Copyright (C) 2016, the P2PSP team.
//  http://www.p2psp.org
//

#include "synchronizer.h"

namespace p2psp {
    Synchronizer::Synchronizer()
    : io_service_(),
    player_socket_(io_service_),
    acceptor_(io_service_)
    {
      player_port = 15000;
    }

    Synchronizer::~Synchronizer()
    {}


    void Synchronizer::Run(int argc, const char* argv[]) throw(boost::system::system_error)
    {
      boost::program_options::options_description desc("This is the synchronizer node of P2PSP.\n");
      desc.add_options()
      ("help", "Produce this help message and exit.")
      ("peers",boost::program_options::value<std::vector<std::string> >(),"Peers list");
      boost::program_options::variables_map vm;
      try{
      boost::program_options::store(boost::program_options::parse_command_line(argc, argv, desc), vm);
      if(argc < 2)
      throw std::exception();
      }
      catch(std::exception& e)
      {
        // If the argument passed is unknown, print the list of available arguments
        std::cout<<desc<<std::endl;
      }
      boost::program_options::notify(vm);
      if(vm.count("help"))
      {
        std::cout<< desc <<std::endl;
      }
      if(vm.count("peers"))
      {
        peer_list = &vm["peers"].as<std::vector<std::string> >();
        // Run the RunThreads function which in turn starts the threads which connect to the peers
        boost::thread(&Synchronizer::RunThreads,this);
      }
    }

    void Synchronizer::RunThreads()
    {
      // Iterarate through the peer_list and start a thread to connect to the peer for every peer in peer_list
      for(std::vector<std::string>::const_iterator it = peer_list->begin();it!=peer_list->end();++it)
      {
        thread_group_.interrupt_all();
        thread_group_.add_thread(new boost::thread(&Synchronizer::ConnectToPeers,this,*it,(it-peer_list->begin())));
        thread_group_.join_all(); //Wait for all threads to complete
      }
    }

    void Synchronizer::ConnectToPeers(std::string s, int id) throw(boost::system::system_error)
    {
        std::vector<std::string> fields;
        boost::algorithm::split(fields,s,boost::is_any_of(":"));
        const boost::asio::ip::address hs = boost::asio::ip::address::from_string(fields[0]);
        unsigned short port = boost::lexical_cast<unsigned short>(fields[1]);
        boost::asio::ip::tcp::endpoint peer(hs,port);
        boost::asio::ip::tcp::socket peer_socket (io_service_);
        peer_socket.connect(peer);
        peer_data[id].resize(1024);
        while(1)
        {
        boost::asio::read(peer_socket,boost::asio::buffer(peer_data[id]));
        if(synchronized)
        {
          std::vector<char> v (peer_data[id].begin(),peer_data[id].begin()+1024);
          mixed_data.insert(v); //Add 1024 bytes of each peer chunk to the set
          peer_data[id].erase(peer_data[id].begin(),peer_data[id].begin()+1024);
        }
        }

    }

    void Synchronizer::Synchronize()
    {
        /*Here we start with a search string and keep on increasing its length until we find a constant offset from the haystack
          string. Once we find the offset, we trim the corresponding peer_data vector according to the offset, so that we achieve
          synchronization. Synchronization is a one time process.
        */
        int start_offset=100,offset=6;
        std::string needle(peer_data[0].begin()+start_offset,peer_data[0].begin()+start_offset+offset);
        for(std::vector<std::vector<char> >::iterator it = peer_data.begin()+1; it!=peer_data.end();++it) //Iterating through all the elements of peer_data vector
        {
            std::string haystack (it->begin(),it->end());
            std::size_t found,found_before;
            while((found=haystack.find(needle))!=std::string::npos && found!=found_before)
            {
                offset++;
                needle = std::string(peer_data[0].begin()+start_offset,peer_data[0].begin()+start_offset+offset); //Incremental length of the search string
                found_before=found; //We stop the loop when the found variable no more changes
            }
            if(found == std::string::npos) //If the string matching fails, continue
            continue;
            it->erase(it->begin(),it->begin()+found); //Trim the first 'found' bytes of the vector
        }
    }

    void Synchronizer::PlayChunk()
    {
      boost::asio::ip::tcp::endpoint player_endpoint (boost::asio::ip::tcp::v4(), player_port);
      acceptor_.open(player_endpoint.protocol());
      acceptor_.set_option(boost::asio::ip::tcp::acceptor::reuse_address(true));
      acceptor_.bind(player_endpoint);
      acceptor_.listen();
      TRACE("Waiting for the player at (" << player_endpoint.address().to_string() << ","
            << std::to_string(player_endpoint.port())
            << ")");
      acceptor_.accept(player_socket_);
      TRACE("The player is ("
            << player_socket_.remote_endpoint().address().to_string() << ","
            << std::to_string(player_socket_.remote_endpoint().port()) << ")");

    }

    void Synchronizer::MixStreams()
    {

    }
}

int main(int argc, const char* argv[])
{
  try {
  p2psp::Synchronizer syn;
  syn.Run(argc, argv);
  }
  catch(boost::system::system_error e)
  {
    TRACE(e.what());
  }
  return -1;
}
