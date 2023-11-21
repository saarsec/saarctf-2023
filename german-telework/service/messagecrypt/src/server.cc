#include <cstdio>
#include <cstdlib>
#include <cinttypes>
#include <unistd.h>
#include <pthread.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <signal.h>

#include "conn_handler.hh"

#include <vector>
using std::vector;

#define SERVICE_PORT 30005
#define SERVICE_MAX_CONN 30

int main() {
	{
		struct sigaction sa {SIG_IGN};
		sigaction(SIGPIPE, &sa, NULL);
	}

	int server_socket = socket(AF_INET, SOCK_STREAM, 0);
	if (server_socket == -1) {
		exit(1);
	}

	{
		int opt = 1;
		int ret1 = setsockopt(
			server_socket, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)
		);
		if (ret1 == -1) {
			exit(1);
		}
		int ret2 = setsockopt(
			server_socket, SOL_SOCKET, SO_REUSEPORT, &opt, sizeof(opt)
		);
		if (ret2 == -1) {
			exit(1);
		}
	}

	struct sockaddr_in server_addr = (struct sockaddr_in) {
		.sin_family = AF_INET,
		.sin_port = htons(SERVICE_PORT),
	};
	if (inet_aton("127.0.0.1", &server_addr.sin_addr) == 0) {
		exit(1);
	}
	if (bind(server_socket, (struct sockaddr*) &server_addr, sizeof(server_addr)) == -1) {
		exit(1);
	}
 
	if (listen(server_socket, SERVICE_MAX_CONN) == -1) {
		exit(1);
	}
 
	
	vector<pthread_t> threads;
	while (1) {
		int connected_socket = accept(server_socket, NULL, NULL);

		{
			struct timeval timeout {
				.tv_sec = 3,
				.tv_usec = 0,
			};
			int ret = setsockopt(
				connected_socket, SOL_SOCKET, SO_RCVTIMEO,
				&timeout, sizeof(timeout)
			);
			if (ret == -1) {
				exit(1);
			}
		}

		{
			threads.push_back(0);
			int ret = pthread_create(&threads.back(), NULL, conn_handler, &connected_socket);
			if (ret != 0) {
				exit(1);
			}
		}

		if (threads.size() > SERVICE_MAX_CONN) {
			vector<pthread_t>::iterator threads_it = threads.begin();
			while (threads_it != threads.end()) {
				int ret = pthread_join(*threads_it, NULL);
				if (ret != 0) {
					exit(1);
				}
				threads_it = threads.erase(threads_it);
			}
		}
	}
 
	return 0;
}