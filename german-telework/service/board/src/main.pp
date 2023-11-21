program Board;

{$mode objfpc}{$H+}

uses
	cthreads, Classes, SysUtils, Sockets, BaseUnix, UnixType, Generics.Collections,
	BoardServerThread, BoardMessageStorage;
type
	TBoardServerThreadList = specialize TObjectList<TBoardServerThread>;
const
	SERVICE_MAX_CONN: Integer = 30;
	SERVICE_PORT: Integer = 30007;
	TV3SECS: timeval = (tv_sec: 3; tv_usec: 0;);
var
	sigAction: SigActionRec;
	serverSocket: Longint;
	connectedSocket: Longint;
	opt: Integer = 1;
	serverAddr: TInetSockAddr;
	threads: TBoardServerThreadList;
	messageStorage: TBoardMessageStorage;
begin
	sigAction := Default(SigActionRec);
	sigAction.sa_handler := sigactionhandler_t(SIG_IGN);
	fpSigAction(SIGPIPE, @sigAction, Nil);

	messageStorage := TBoardMessageStorage.Create;

	serverSocket := fpSocket(AF_INET, SOCK_STREAM, 0);
	if serverSocket < 0 then begin
		Exit;
	end;
	
	if fpSetSockOpt(serverSocket, SOL_SOCKET, SO_REUSEADDR, @opt, sizeOf(opt)) < 0 then begin
		Exit;
	end;
	if fpSetSockOpt(serverSocket, SOL_SOCKET, SO_REUSEPORT, @opt, sizeOf(opt)) < 0 then begin
		Exit;
	end;
	
	serverAddr.sin_family := AF_INET;
	serverAddr.sin_port := htons(SERVICE_PORT);
	serverAddr.sin_addr.s_addr := htonl($7F000001); 
	if fpBind(serverSocket, @serverAddr, sizeOf(serverAddr)) < 0 then begin
		Exit;
	end;

	if fpListen(serverSocket, SERVICE_MAX_CONN) < 0 then begin
		Exit;
	end;


	threads := TBoardServerThreadList.Create;
	while true do begin
		connectedSocket := fpAccept(serverSocket, Nil, Nil);
		if connectedSocket < 0 then begin
			Exit;
		end;

		if fpSetSockOpt(connectedSocket, SOL_SOCKET, SO_RCVTIMEO, @TV3SECS, sizeOf(timeval)) < 0 then begin
			Exit;
		end;

		threads.Add(TBoardServerThread.Create(connectedSocket, messageStorage));

		if threads.Count > SERVICE_MAX_CONN then begin 
			while threads.Count > 0 do begin
				if threads.First.Finished = false then begin
					threads.First.WaitFor();
				end;
				threads.Delete(0);
			end;
		end;
	end;
	threads.Free;
	messageStorage.Free;
end.
