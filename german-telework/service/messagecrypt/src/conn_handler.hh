#pragma once
#include <cassert>
#include <string>
#include <vector>
#include <optional>
#include <cstdint>
#include <stdexcept>
#include <pthread.h>
#include <unistd.h>
#include <sys/socket.h>

#include "magenta.hh"
#include "keystore.hh"
#include "base64.hh"

#include "transport_crypt.hh"
#include "telework_types.hh"

void* conn_handler(void* param);