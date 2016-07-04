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
    {
      player_socket_(io_service_);
      acceptor_(io_service_);

    }


    void Synchronizer::Run(int argc, const char* argv[]) throw(boost::system::system_error)
    {
      boost::program_options::options_description desc("This is the synchronizer node of P2PSP.\n");
      desc.add_options()
      ("help", "Produce this help message and exit.")
      ("peers",boost::program_options::value<std::vector<std::string> >(),"Peers list");
      boost::program_options::variables_map vm;
      try{
      boost::program_options::store(boost::program_options::parse_command_line(argc, argv, desc), vm);
      }
      catch(std::exception e)
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
        thread_group_.add_thread(new boost::thread(&Synchronizer::ConnectToPeers,this,*it));
        thread_group_.join_all(); //Wait for all threads to complete
      }
    }

    void Synchronizer::ConnectToPeers(std::string)
    {

    }

}
