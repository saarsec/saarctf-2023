cmake_minimum_required(VERSION 3.21)
project(turingcode)

set(CMAKE_CXX_STANDARD 17)

set(CMAKE_CXX_FLAGS "-O1")

add_executable(turingcode main.cpp turingmachine.h)

#[[
include(CheckIPOSupported)
check_ipo_supported(RESULT supported OUTPUT error)

if( supported )
	message(STATUS "IPO / LTO enabled")
	set_property(TARGET turingcode PROPERTY INTERPROCEDURAL_OPTIMIZATION TRUE)
else()
	message(STATUS "IPO / LTO not supported: <${error}>")
endif()
]]
