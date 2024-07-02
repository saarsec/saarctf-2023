# saarCTF 2023

Services from [saarCTF 2023](https://ctftime.org/event/2049).

## Building services
Enter a service directory and use `docker-compose`, e.g.:
```bash
cd pasteable
docker-compose up --build -d
```

## Running checkers
Every service comes with a `checkers` directory, which contains a python-script named after the service.
Running this script should place three flags in the service and try to retrieve them subsequently.
Caveat: Make sure the `gamelib` is in the `PYTHONPATH`, e.g.:
```bash
PYTHONPATH=.. python3 bytewarden.py [<ip>]
```

Checkers require a Redis instance to store information between ticks. 
If you don't have redis installed locally, use the environment variables `REDIS_HOST` and `REDIS_DB` to configure one.


## Flag IDs and exploits
The script `get_flag_ids.py` prints you the flag ids used to store the demo flags.

Each service comes with demo exploits to show the vulnerability.
To run an exploit: `python3 exploit_file.py <ip> [<flag-id>]`


## Services
- [Django Bells](./django-bells) | [Writeup](https://saarsec.rocks/2023/11/18/saarCTF-djangobells.html)
- [German Telework](./german-telework) | [Writeup](https://saarsec.rocks/2023/11/20/saarCTF-German-Telework.html)
- [Pasteable](./pasteable) | [Writeup](https://saarsec.rocks/2023/11/25/saarCTF-Pasteable.html)
- [RedisBBQ](./redis-bbq) | [Service Explanation](./redis-bbq/README.md)
- [SaaSSaaSSaaSSaaS](./SaaSSaaSSaaSSaaS) | [Writeup](https://saarsec.rocks/2023/11/19/saarCTF-SaaSSaaSSaaSSaaS.html)
- [TuringMachines](./turing-machines) | [Exploit Walkthrough](./turing-machines/exploits/README.md)
