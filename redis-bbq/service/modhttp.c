#define _GNU_SOURCE

#include "redismodule.h"
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/wait.h>


// IMPORT two more functions from redis
struct client;
typedef struct client client;

client *moduleGetReplyClient(RedisModuleCtx *ctx);

void addReplyProto(client *c, const char *s, size_t len);

__attribute__((weak))
client *moduleGetReplyClient(RedisModuleCtx *ctx) { return NULL; }

__attribute__((weak))
void addReplyProto(client *c, const char *s, size_t len) {
	fprintf(stderr, "[ERROR] addReplyProto not bound!\n");
}

void RedisModule_ReplyWithHTTPHeader(RedisModuleCtx *ctx, int ok, int headers) {
	client *c = moduleGetReplyClient(ctx);
	if (!c)
		return;
	if (ok && headers) {
		addReplyProto(c, "HTTP/1.1 200 OK\r\n", 17);
	} else if (ok && !headers) {
		addReplyProto(c, "HTTP/1.1 200 OK\r\n\r\n", 19);
	} else {
		addReplyProto(c, "HTTP/1.1 400 NOT OK\r\n\r\n", 23);
	}
}

// IMPORT END



static long string_distance(const char *s1, size_t s1_len, const char *s2, size_t s2_len) {
	long distance = 0;
	for (size_t i = 0; i < s1_len && i < s2_len; i++) {
		if (s1[i] != s2[i]) distance++;
	}
	return distance;
}

static int name_valid(const char *s, size_t len) {
	if (!s || len > 64)
		return 0;
	for (size_t i = 0; i < len; i++) {
		if (s[i] >= '0' && s[i] <= '9')
			continue;
		if (s[i] >= 'A' && s[i] <= 'Z')
			continue;
		if (s[i] >= 'a' && s[i] <= 'z')
			continue;
		if (s[i] == '-' || s[i] == '_')
			continue;
		return 0;
	}
	return 1;
}


int HttpGet_RedisCommand(RedisModuleCtx *ctx, RedisModuleString **argv, int argc) {
	RedisModule_AutoMemory(ctx);
	if (argc < 2) {
		return RedisModule_WrongArity(ctx);
	}

	RedisModuleCallReply *reply = RedisModule_Call(ctx, "LEGACY_GET", "s", argv[1]);
	if (argc == 3) {
		RedisModule_ReplyWithHTTPHeader(
				ctx,
				RedisModule_CallReplyType(reply) != REDISMODULE_REPLY_NULL,
				RedisModule_CallReplyType(reply) == REDISMODULE_REPLY_STRING
		);
	}
	RedisModule_ReplyWithCallReply(ctx, reply);

	return REDISMODULE_OK;
}

int HttpPost_RedisCommand(RedisModuleCtx *ctx, RedisModuleString **argv, int argc) {
	if (argc == 3) {
		RedisModule_ReplyWithHTTPHeader(ctx, 1, 0);
	}
	return REDISMODULE_OK;
}

int NewUser_RedisCommand(RedisModuleCtx *ctx, RedisModuleString **argv, int argc) {
	RedisModule_AutoMemory(ctx);
	if (argc != 3) {
		return RedisModule_WrongArity(ctx);
	}

	size_t username_len;
	const char *username = RedisModule_StringPtrLen(argv[1], &username_len);
	if (!name_valid(username, username_len)) {
		RedisModule_ReplyWithError(ctx, "Invalid username");
		return REDISMODULE_ERR;
	}
	size_t password_len;
	const char *password = RedisModule_StringPtrLen(argv[2], &password_len);
	if (!name_valid(password, password_len)) {
		RedisModule_ReplyWithError(ctx, "Invalid password");
		return REDISMODULE_ERR;
	}

	char *user_name_key;
	size_t user_name_key_len = asprintf(&user_name_key, "user:%s:name", username);
	RedisModuleCallReply *reply = RedisModule_Call(ctx, "EXISTS", "b", user_name_key, user_name_key_len);
	if (RedisModule_CallReplyType(reply) != REDISMODULE_REPLY_INTEGER || RedisModule_CallReplyInteger(reply) != 0) {
		RedisModule_ReplyWithError(ctx, "User already exists");
		return REDISMODULE_ERR;
	}

	char *keys, *redis_password;
	size_t keys_len = asprintf(&keys, "~user:%s:*", username);
	size_t redis_password_len = asprintf(&redis_password, ">%s", password);
	reply = RedisModule_Call(
			ctx, "ACL", "csccccccccccccccccccbbccccc", "SETUSER", argv[1],
			"on", "-@all", "+@read", "-@hash", "+SETNX", "+SADD", "+LPUSH", "+HSETNX", "+INCRBY", "+@connection", "+@pubsub",
			"-@dangerous", "-scan", "-psubscribe", "-pubsub", "+http.post", "+client", "+firealarm",
			redis_password, redis_password_len, keys, keys_len, "~party:*", "~fire:*", "~country:*", "~newest:*", "allchannels"
	);
	free(keys);
	free(redis_password);
	if (RedisModule_CallReplyType(reply) == REDISMODULE_REPLY_ERROR) {
		free(user_name_key);
		RedisModule_ReplyWithCallReply(ctx, reply);
		return REDISMODULE_ERR;
	}
	RedisModule_Call(ctx, "ACL", "c", "SAVE");
	RedisModule_Call(ctx, "SET", "bb", user_name_key, user_name_key_len, username, username_len);

	free(user_name_key);
	RedisModule_ReplyWithCallReply(ctx, reply);
	return REDISMODULE_OK;
}

int FireAlarm_RedisCommand(RedisModuleCtx *ctx, RedisModuleString **argv, int argc) {
	RedisModule_AutoMemory(ctx);
	if (argc != 2) {
		return RedisModule_WrongArity(ctx);
	}

	RedisModuleCallReply *reply = RedisModule_Call(ctx, "HMGET", "sccc", argv[1], "country", "location", "content");
	if (RedisModule_CallReplyType(reply) != REDISMODULE_REPLY_ARRAY) {
		RedisModule_ReplyWithError(ctx, "Key has invalid type");
		return REDISMODULE_ERR;
	}
	const char *fire_data[3];
	size_t fire_data_len[3];
	for (int i = 0; i < 3; i++) {
		RedisModuleCallReply *reply_element = RedisModule_CallReplyArrayElement(reply, i);
		if (RedisModule_CallReplyType(reply_element) != REDISMODULE_REPLY_STRING) {
			RedisModule_ReplyWithError(ctx, "Key field has invalid type");
			return REDISMODULE_ERR;
		}
		fire_data[i] = RedisModule_CallReplyStringPtr(reply_element, &fire_data_len[i]);
	}

	if (fire_data_len[0] != 12 || fire_data_len[1] != 16) {
		RedisModule_ReplyWithError(ctx, "Fire has data of invalid length");
		return REDISMODULE_ERR;
	}
	char *json, *country_key;
	size_t json_len = asprintf(&json, "{\"country\":\"%.*s\",\"location\":\"%.*s\"}", (int) fire_data_len[0], fire_data[0], (int) fire_data_len[1], fire_data[1]);
	size_t country_key_length = asprintf(&country_key, "country:%.*s:firefighters", (int) fire_data_len[0], fire_data[0]);

	reply = RedisModule_Call(ctx, "HGETALL", "b", country_key, country_key_length);
	if (RedisModule_CallReplyType(reply) != REDISMODULE_REPLY_ARRAY) {
		RedisModule_ReplyWithError(ctx, "Country firefighters key has invalid type");
		return REDISMODULE_ERR;
	}
	RedisModule_ReplyWithArray(ctx, REDISMODULE_POSTPONED_ARRAY_LEN);
	long count_firefighters = 0;
	for (size_t i = 0; i + 1 < RedisModule_CallReplyLength(reply); i += 2) {
		RedisModuleCallReply *ff_username = RedisModule_CallReplyArrayElement(reply, i);
		RedisModuleCallReply *ff_location_json = RedisModule_CallReplyArrayElement(reply, i + 1);
		if (RedisModule_CallReplyType(ff_username) == REDISMODULE_REPLY_STRING &&
			RedisModule_CallReplyType(ff_location_json) == REDISMODULE_REPLY_STRING) {
			size_t ff_location_json_str_len, ff_username_str_len;
			const char *ff_location_json_str = RedisModule_CallReplyStringPtr(ff_location_json, &ff_location_json_str_len);
			if (ff_location_json_str_len == 56) {
				long distance = string_distance(json, json_len, ff_location_json_str, ff_location_json_str_len);
				if (distance <= 2) {
					// Notify this firefigher, near fire position
					const char *ff_username_str = RedisModule_CallReplyStringPtr(ff_username, &ff_username_str_len);
					if (ff_username_str_len > 255)
					    continue;
					char *alarm_key;
					size_t alarm_key_len = asprintf(&alarm_key, "user:%.*s:alarms", (int) ff_username_str_len, ff_username_str);
					RedisModule_Call(ctx, "LPUSH", "bbbb", alarm_key, alarm_key_len,
									 fire_data[2], fire_data_len[2],
									 fire_data[1], fire_data_len[1],
									 fire_data[0], fire_data_len[0]
					);
					free(alarm_key);
					RedisModule_ReplyWithCallReply(ctx, ff_username);
					RedisModule_ReplyWithCallReply(ctx, ff_location_json);
					count_firefighters++;
				}
			}
		}
	}
	RedisModule_ReplySetArrayLength(ctx, count_firefighters * 2);

	free(json);
	free(country_key);

	return REDISMODULE_OK;
}


void HttpFilter(RedisModuleCommandFilterCtx *filter) {
	RedisModuleString *commandStr = RedisModule_CommandFilterArgGet(filter, 0);
	size_t length;
	const char *command = RedisModule_StringPtrLen(commandStr, &length);
	if (length == 3 && strncmp(command, "GET", length) == 0) {
		RedisModule_CommandFilterArgReplace(filter, 0, RedisModule_CreateString(NULL, "http.GET", 8));
	} else if (length == 4 && strncmp(command, "POST", length) == 0) {
		RedisModule_CommandFilterArgReplace(filter, 0, RedisModule_CreateString(NULL, "http.POST", 9));
	} else if (length == 5 && strncmp(command, "Host:", length) == 0) {
		RedisModule_CommandFilterArgReplace(filter, 0, RedisModule_CreateString(NULL, "NOP", 3));
	}
}


static void child_process_exit_handler(int sig) {
    waitpid(-1, NULL, WNOHANG);
}


__attribute__((unused)) int RedisModule_OnLoad(RedisModuleCtx *ctx, RedisModuleString **argv, int argc) {
    signal(SIGCHLD, child_process_exit_handler);

	if (RedisModule_Init(ctx, "http", 1, REDISMODULE_APIVER_1) == REDISMODULE_ERR)
		return REDISMODULE_ERR;

	RedisModule_RegisterCommandFilter(ctx, HttpFilter, REDISMODULE_CMDFILTER_NOSELF);

	if (RedisModule_CreateCommand(ctx, "http.GET", HttpGet_RedisCommand, "fast readonly", 0, 0, 0) == REDISMODULE_ERR)
		return REDISMODULE_ERR;
	if (RedisModule_CreateCommand(ctx, "http.POST", HttpPost_RedisCommand, "fast", 0, 0, 0) == REDISMODULE_ERR)
		return REDISMODULE_ERR;
	if (RedisModule_CreateCommand(ctx, "NEWUSER", NewUser_RedisCommand, "write admin", 0, 0, 0) == REDISMODULE_ERR)
		return REDISMODULE_ERR;
	if (RedisModule_CreateCommand(ctx, "FIREALARM", FireAlarm_RedisCommand, "write", 0, 0, 0) == REDISMODULE_ERR)
		return REDISMODULE_ERR;

	return REDISMODULE_OK;
}
