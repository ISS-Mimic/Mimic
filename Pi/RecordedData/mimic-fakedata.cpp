#include <fstream>
#include <iostream>
#include <map>
#include <chrono>
#include <string>
#include <deque>
#include <thread>
#include <sstream>
#include <boost/lexical_cast.hpp>
#include <sqlite3.h>

int
main( int argc, char *argv[] )
{
  if ( argc != 2 )
  {
    std::cerr << "Usage: a.out path" << std::endl;
    return 1;
  }

  std::string path = argv[1];

  double factor = 1.0;

  std::deque< std::string > filesToRead;

  std::multimap< double, std::pair< std::string, double > > masterDataList;

  filesToRead.push_back( "AIRLOCK000001" );
filesToRead.push_back( "AIRLOCK000002" );
filesToRead.push_back( "AIRLOCK000003" );
filesToRead.push_back( "AIRLOCK000004" );
filesToRead.push_back( "AIRLOCK000005" );
filesToRead.push_back( "AIRLOCK000006" );
filesToRead.push_back( "AIRLOCK000007" );
filesToRead.push_back( "AIRLOCK000008" );
filesToRead.push_back( "AIRLOCK000009" );
filesToRead.push_back( "AIRLOCK000010" );
filesToRead.push_back( "AIRLOCK000011" );
filesToRead.push_back( "AIRLOCK000012" );
filesToRead.push_back( "AIRLOCK000013" );
filesToRead.push_back( "AIRLOCK000014" );
filesToRead.push_back( "AIRLOCK000015" );
filesToRead.push_back( "AIRLOCK000016" );
filesToRead.push_back( "AIRLOCK000017" );
filesToRead.push_back( "AIRLOCK000018" );
filesToRead.push_back( "AIRLOCK000049" );
filesToRead.push_back( "AIRLOCK000054" );
filesToRead.push_back( "AIRLOCK000055" );
filesToRead.push_back( "AIRLOCK000056" );
filesToRead.push_back( "AIRLOCK000057" );
filesToRead.push_back( "NODE2000001" );
filesToRead.push_back( "NODE2000002" );
filesToRead.push_back( "NODE2000006" );
filesToRead.push_back( "NODE2000007" );
filesToRead.push_back( "NODE3000004" );
filesToRead.push_back( "NODE3000005" );
filesToRead.push_back( "NODE3000008" );
filesToRead.push_back( "NODE3000009" );
filesToRead.push_back( "NODE3000011" );
filesToRead.push_back( "NODE3000012" );
filesToRead.push_back( "NODE3000013" );
filesToRead.push_back( "NODE3000017" );
filesToRead.push_back( "NODE3000019" );
filesToRead.push_back( "P1000001" );
filesToRead.push_back( "P1000002" );
filesToRead.push_back( "P1000003" );
filesToRead.push_back( "P1000004" );
filesToRead.push_back( "P1000005" );
filesToRead.push_back( "P4000001" );
filesToRead.push_back( "P4000002" );
filesToRead.push_back( "P4000004" );
filesToRead.push_back( "P4000005" );
filesToRead.push_back( "P4000007" );
filesToRead.push_back( "P4000008" );
filesToRead.push_back( "P6000001" );
filesToRead.push_back( "P6000002" );
filesToRead.push_back( "P6000004" );
filesToRead.push_back( "P6000005" );
filesToRead.push_back( "P6000007" );
filesToRead.push_back( "P6000008" );
filesToRead.push_back( "S0000001" );
filesToRead.push_back( "S0000002" );
filesToRead.push_back( "S0000003" );
filesToRead.push_back( "S0000004" );
filesToRead.push_back( "S0000005" );
filesToRead.push_back( "S0000008" );
filesToRead.push_back( "S0000009" );
filesToRead.push_back( "S1000001" );
filesToRead.push_back( "S1000002" );
filesToRead.push_back( "S1000003" );
filesToRead.push_back( "S1000004" );
filesToRead.push_back( "S1000005" );
filesToRead.push_back( "S4000001" );
filesToRead.push_back( "S4000002" );
filesToRead.push_back( "S4000004" );
filesToRead.push_back( "S4000005" );
filesToRead.push_back( "S4000007" );
filesToRead.push_back( "S4000008" );
filesToRead.push_back( "S6000001" );
filesToRead.push_back( "S6000002" );
filesToRead.push_back( "S6000004" );
filesToRead.push_back( "S6000005" );
filesToRead.push_back( "S6000007" );
filesToRead.push_back( "S6000008" );
filesToRead.push_back( "USLAB000006" );
filesToRead.push_back( "USLAB000007" );
filesToRead.push_back( "USLAB000008" );
filesToRead.push_back( "USLAB000009" );
filesToRead.push_back( "USLAB000010" );
filesToRead.push_back( "USLAB000016" );
filesToRead.push_back( "USLAB000018" );
filesToRead.push_back( "USLAB000019" );
filesToRead.push_back( "USLAB000020" );
filesToRead.push_back( "USLAB000021" );
filesToRead.push_back( "USLAB000022" );
filesToRead.push_back( "USLAB000023" );
filesToRead.push_back( "USLAB000024" );
filesToRead.push_back( "USLAB000025" );
filesToRead.push_back( "USLAB000026" );
filesToRead.push_back( "USLAB000027" );
filesToRead.push_back( "USLAB000028" );
filesToRead.push_back( "USLAB000029" );
filesToRead.push_back( "USLAB000030" );
filesToRead.push_back( "USLAB000031" );
filesToRead.push_back( "USLAB000032" );
filesToRead.push_back( "USLAB000033" );
filesToRead.push_back( "USLAB000034" );
filesToRead.push_back( "USLAB000035" );
filesToRead.push_back( "USLAB000036" );
filesToRead.push_back( "USLAB000037" );
filesToRead.push_back( "USLAB000038" );
filesToRead.push_back( "USLAB000040" );
filesToRead.push_back( "USLAB000043" );
filesToRead.push_back( "USLAB000044" );
filesToRead.push_back( "USLAB000045" );
filesToRead.push_back( "USLAB000046" );
filesToRead.push_back( "USLAB000047" );
filesToRead.push_back( "USLAB000048" );
filesToRead.push_back( "USLAB000049" );
filesToRead.push_back( "USLAB000050" );
filesToRead.push_back( "USLAB000051" );
filesToRead.push_back( "USLAB000052" );
filesToRead.push_back( "USLAB000053" );
filesToRead.push_back( "USLAB000054" );
filesToRead.push_back( "USLAB000055" );
filesToRead.push_back( "USLAB000056" );
filesToRead.push_back( "USLAB000057" );
filesToRead.push_back( "USLAB000058" );
filesToRead.push_back( "USLAB000059" );
filesToRead.push_back( "USLAB000060" );
filesToRead.push_back( "USLAB000061" );
filesToRead.push_back( "USLAB000081" );
filesToRead.push_back( "USLAB000082" );
filesToRead.push_back( "USLAB000083" );
filesToRead.push_back( "USLAB000084" );
filesToRead.push_back( "USLAB000095" );
filesToRead.push_back( "USLAB000096" );
filesToRead.push_back( "USLAB000097" );
filesToRead.push_back( "USLAB000102" );
filesToRead.push_back( "Z1000001" );
filesToRead.push_back( "Z1000002" );
filesToRead.push_back( "Z1000003" );
filesToRead.push_back( "Z1000004" );
filesToRead.push_back( "Z1000005" );
filesToRead.push_back( "Z1000006" );
filesToRead.push_back( "Z1000007" );
filesToRead.push_back( "Z1000008" );
filesToRead.push_back( "Z1000009" );
filesToRead.push_back( "Z1000010" );
filesToRead.push_back( "Z1000011" );
filesToRead.push_back( "Z1000012" );
filesToRead.push_back( "Z1000013" );
filesToRead.push_back( "Z1000014" );
filesToRead.push_back( "Z1000015" );
  
  // Load all the data into the master data list
  for ( const auto & file : filesToRead )
  {
    std::ifstream infile;
    infile.open( path + "/" + file + ".txt" );
    while ( true )
    {
      double time;
      double value;

      infile >> time;
      if ( !infile.good() ) break;

      infile >> value;
      if ( !infile.good() ) break;

      masterDataList.emplace( time, std::pair< std::string, double >( file, value ) );
    }
    infile.close();
    infile.clear();
  }

  sqlite3 * database;

  int result = sqlite3_open("/dev/shm/iss_telemetry.db", &database );
  if ( result != SQLITE_OK )
  {
    std::cerr << "Couldn't open database." << std::endl;
    std::cerr << "Message: " << sqlite3_errstr( result ) << std::endl;
    return 1;
  }

  auto iter = masterDataList.begin();

  double dataEpoch = iter->first;

  std::chrono::steady_clock::time_point programEpoch = std::chrono::steady_clock::now();

  std::chrono::steady_clock::time_point programNow;

  std::chrono::duration< double > elapsedTime;

  // Write the stuff out.
  while ( iter != masterDataList.end() )
  {
    programNow = std::chrono::steady_clock::now();

    // Time in seconds
    elapsedTime = std::chrono::duration_cast< std::chrono::duration< double > > ( programNow - programEpoch );

    double nowTimeStamp = factor * elapsedTime.count() / 3600.0 + dataEpoch;

    // Only advance the iterator if we pass the time stamp
    while ( iter != masterDataList.end() && nowTimeStamp >= iter->first )
    {
      std::string statement = "UPDATE telemetry set Value = " + boost::lexical_cast< std::string > ( iter->second.second )
                            + " where ID = \"" + boost::lexical_cast< std::string > ( iter->second.first ) + "\"";

      char * message;
#ifdef DEBUG
      std::cout << statement << std::endl;
#else      
      result = sqlite3_exec( database, statement.c_str(), NULL, NULL, &message );

      if ( result != SQLITE_OK )
      {
        std::cerr << "Sqlite3 error: " << message << std::endl;
        sqlite3_free( message );
      }
#endif      
      ++iter;
    }
    std::this_thread::sleep_for( std::chrono::milliseconds( 100 ) ); // or whatever
  }

  sqlite3_close( database );
  std::cout << "Done." << std::endl;
  return 0;
}
