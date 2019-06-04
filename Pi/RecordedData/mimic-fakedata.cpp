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
main(  )
{
  const double factor = 1.0;

  std::deque< std::string > filesToRead;

  std::multimap< double, std::pair< std::string, double > > masterDataList;

  filesToRead.push_back( "P0000001" );
  // TODO: fill this out


  // Load all the data into the master data list
  for ( const auto & file : filesToRead )
  {
    std::ifstream infile;
    infile.open( file + ".txt" );
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
                            + " where Label = " + boost::lexical_cast< std::string > ( iter->second.first );

      char * message;
      result = sqlite3_exec( database, statement.c_str(), NULL, NULL, &message );

      if ( result != SQLITE_OK )
      {
        std::cerr << "Sqlite3 error: " << message << std::endl;
        sqlite3_free( message );
      }
      ++iter;
    }
    std::this_thread::sleep_for( std::chrono::milliseconds( 100 ) ); // or whatever
  }

  sqlite3_close( database );
  std::cout << "Done." << std::endl;
  return 0;
}
