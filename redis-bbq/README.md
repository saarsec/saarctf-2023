# RedisBBQ

RedisBBQ is Redis, but turned into a HTTP server. To this end, a C module adds custom commands like "GET" or "POST".

Keys starting with '/' contain HTTP headers and HTML code, which Redis will happily serve.



## Users and Vulnerability 1 (improper access checking)
The database contains these keys for user management:
```
user:<username>:name
user:<username>:dishes
user:<username>:dishes_cooked
user:<username>:alarms          // pubsub channel for firefighter alarms
user:<username>:watch_locations // list of registered locations as JSON
newest:users                    // list, append new names at the beginning
```

Flag #1 is in `user:<username>:dishes`. Every user has the permission `~user:<username>:*`, so he can access its own key only.
However, the HTTP get is not limited to `/...`, and while it uses the regular GET command itself, this command instance is not permission-checked.

See [exploits/exploit_get.py] for a full exploit implementation.



## Partys and Vulnerability 2 (`TRACKING BCAST` mode)
The database contains partys in these keys:
```
party:<uuid>:name
party:<uuid>:organisator
party:<uuid>:guests
party:<uuid>:food     // flag is here
party:<uuid>:fire_id
PUBLISH/SUBSCRIBE on who_brings_what
```
Everybody has read access to these keys, but you cannot list keys (`KEYS`, `SCAN` etc are forbidden). Thus the `uuid` of each party serves as a secret. Flag #2 is contained in each party's food list.

However, Redis contains functionality to get informed about changes of a set of keys, and this command allows broadcasts.
The relevant command is: `CLIENT TRACKING on REDIRECT <client-id> BCAST PREFIX party:` - redis will now inform you about every new party that the gameserver creates.

See [exploits/exploit_tracking_commands.py] for the full exploit.

There was an unintended vulnerability here: the command `RANDOMKEY` could indeed leak party UUIDs.



## Firefighting and Vulnerability 3 (`strcmp` and 0-bytes)
The database contains mechanisms to assign firefighters to fire alerts.
```
country:<country>:fires         // list of fires, readable
country:<country>:firefighters  // hashmap of (username: "json-string"), not readable

fire:<id>        hash: {country:xyz, location:abc, content:"..."}
fire:<id>:wood   => INCR until some treshold, then firefighters get triggered
//fire:country   => access doesn't matter
//fire:location  => no read
//fire:content   => list of burning stuff, including flag3 // append-only, no read

newest:firefighters  // list, append new names at the beginning
newest:countries     // list, append new countries at the beginning
```

Flag #3 is in the fire's content. Commands that read maps are forbidden, so you cannot directly read the flag from the fire. But when you're a firefighter near the fire's location, you'll receive all information by triggering the `FIREALARM <id>` command. We can get the gameserver's firefighter location by playing with the C code and 0 bytes:

1. We know the country from the `newest:countries` key but not the location
2. Create a fire whose location starts with a 0-byte (which is legal, Redis strings are byte strings)
3. Trigger the fire alarm for your fire. You'll receive a list with *all* firefighters from the country.
4. Create a new firefighter at the known locations.
5. Trigger the fire alarm for the target fire again, your firefighter will receive the warning.

Why does that work? `asprintf` in line 174 interprets your location as C string, it will thus generate a JSON of the form `{"country":"<...>","location":""}`. The string distance between this string and any other location JSON is 2 (the final `"}`) because the comparison stops after the shorter string. Thus the check in line 193 will always be true, and you receive all firefighters with their locations.

There was another unintended Vulnerability here: the allowed command `DUMP` allows reading from many datastructures, including maps. So getting this flag was much easier than expected.



## Vulnerability 4 (DoS)
The command `NEWUSER` could actually overwrite the default user, given the username `default`. This renders the service inaccessible, because no HTTP connections can be made, and no new users can be created.

Some teams have chosen to use this vulnerability to take down the service on unpatched teams. Not sure if this was clever, because the gameserver couldn't store new flags in such a broken service, and the DoSing team could no longer steal flags from them.
