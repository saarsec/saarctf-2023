unit BoardServerThread;

{$mode objfpc}{$H+}

interface

uses
	Classes, Sockets, BaseUnix, SysUtils, StrUtils, Types,
	BoardTypes, BoardMessageStorage, TransportCrypt;

type
	TBoardServerThread = class(TThread)
		private
			connectedSocket: Longint;
			messageStorage: TBoardMessageStorage;
			function ParseTeleworkData(teleworkUserSerialized: AnsiString): TTeleworkUserRecord;
			function ParseCommand(commandSerialized: AnsiString): TCommandRecord;
			function SerializeDataRecords(userRecord: TTeleworkUserRecord): AnsiString;
		protected
			procedure Execute; override;
		public
			constructor Create(_connectedSocket: Longint; _messageStorage: TBoardMessageStorage);
	end;
const
	NEWLN: Char = #10;
	CHUNK_SIZE = 255;

implementation

constructor TBoardServerThread.Create(_connectedSocket: Longint; _messageStorage: TBoardMessageStorage);
begin
	FreeOnTerminate := false;
	connectedSocket := _connectedSocket;
	messageStorage := _messageStorage;
	inherited Create(false);
end;

function TBoardServerThread.ParseTeleworkData(teleworkUserSerialized: AnsiString): TTeleworkUserRecord;
var
	user: TTeleworkUserRecord;
	parts: TStringDynArray;
	part: AnsiString = '';
	userRecord: AnsiString = '';
begin
	user.Error := true;

	parts := SplitString(teleworkUserSerialized, '||');
	for part in parts do begin
		if (userRecord = '') and (Length(part) >= 2) and StartsStr('0|', part) then begin
			userRecord := part;
		end else begin
			user.Remainder := user.Remainder + '||' + part;
		end;
	end;

	if (userRecord = '') then begin
		Result := user; Exit;
	end;
	
	parts := SplitString(userRecord, '|');
	if length(parts) <> 7 then begin
		Result := user; Exit;
	end;

	if parts[0] <> '0' then begin
		Result := user; Exit;
	end;

	user.FirstName := parts[1];
	user.LastName := parts[2];
	user.Password := parts[3];
	user.EmployeeID := parts[4];
	user.JobDesc := parts[5];

	if user.EmployeeID = '' then begin
		Result := user; Exit;
	end;

	try
		user.HolidaysLeft := StrToInt(parts[6]);
	except
		on Exception: EConvertError do begin
			Result := user; Exit;
		end
	end;

	user.Error := false;
	Result := user;
end;

function TBoardServerThread.ParseCommand(commandSerialized: AnsiString): TCommandRecord;
var
	command: TCommandRecord;
	parts: TStringDynArray;
	tmpInt: LongInt;
begin
	command.Error := true;

	parts := SplitString(commandSerialized, '|');
	if length(parts) < 1 then begin
		Result := command; Exit;
	end;

	if parts[0] = 'c' then begin 
		command.ActionID := parts[0];
	end else if parts[0] = 'n' then begin 
		command.ActionID := parts[0];
		if length(parts) <> 2 then begin
			Result := command; Exit;
		end;
		if ((TryStrToInt(parts[1], tmpInt) = false) or (tmpInt < 0)) then begin
			Result := command; Exit;
		end;
		command.Data := parts[1];
	end else if parts[0] = 'i' then begin 
		command.ActionID := parts[0];
		if length(parts) <> 2 then begin
			Result := command; Exit;
		end;
		command.Data := parts[1];
	end else if parts[0] = 'p' then begin 
		command.ActionID := parts[0];
		if length(parts) <> 2 then begin
			Result := command; Exit;
		end;
		if length(parts[1]) > 1000 then begin
			Result := command; Exit;
		end;
		command.Data := parts[1];
	end else begin 
		Result := command; Exit;
	end;
	command.Error := false;
	Result := command;
end;

function TBoardServerThread.SerializeDataRecords(userRecord: TTeleworkUserRecord): AnsiString;
begin
	Result := '0|' + 
		userRecord.FirstName + '|' + 
		userRecord.LastName + '|' + 
		userRecord.Password + '|' +
		userRecord.EmployeeID + '|' +
		userRecord.JobDesc + '|' +
		IntToStr(userRecord.HolidaysLeft);
	if userRecord.Remainder <> '' then begin
		Result := Result + userRecord.Remainder;
	end;
end;

procedure TBoardServerThread.Execute;
label
	sendCode, finish, endThread;
var
	errorCode: UInt16 = 0;
	bytes: Int64 = 0;
	buffer: String[CHUNK_SIZE] = '';
	receivedStr: AnsiString = '';
	receivedStrParts: TStringDynArray;
	userRecord: TTeleworkUserRecord;
	commandRecord: TCommandRecord;
	serialized: AnsiString;
	tcStateRecv: TTransportCryptState;
	tcStateSend: TTransportCryptState;
	newlnCopy: Char;
	messageAndError: TMessageAndError;
begin
	tcStateRecv := TTransportCryptState.Create;
	while true do begin
		buffer := '';
		bytes := fpRecv_tc_state(@tcStateRecv, connectedSocket, PUInt8(@buffer)+1, CHUNK_SIZE, 0);
		if bytes < 0 then begin
			goto endThread;
		end;
		SetLength(buffer, bytes);
		receivedStr := receivedStr + buffer;
		if ((Length(receivedStr) > 0) and (RightStr(receivedStr, 1) = NEWLN)) or (bytes < CHUNK_SIZE) then begin
			Break;
		end;
	end;
	tcStateRecv.Free;
	tcStateSend := TTransportCryptState.Create;	

	receivedStr := TrimRight(receivedStr);

	receivedStrParts := SplitString(receivedStr, '|||');

	if length(receivedStrParts) <> 3 then begin
		errorCode := $5301;
		goto sendCode;
	end;

	if receivedStrParts[0] <> '3' then begin
		errorCode := $5302;
		goto sendCode;
	end;

	userRecord := ParseTeleworkData(receivedStrParts[1]);
	if userRecord.Error = true then begin
		errorCode := $5303;
		goto sendCode;
	end;

	commandRecord := parseCommand(receivedStrParts[2]);
	if commandRecord.Error = true then begin
		errorCode := $5304;
		goto sendCode;
	end;
	
	if (commandRecord.ActionID = 'c') or (commandRecord.ActionID = 'n') or (commandRecord.ActionID = 'i') or (commandRecord.ActionID = 'p') then begin
		if commandRecord.ActionID = 'c' then begin
			serialized := IntToStr(messageStorage.GetCount);
		end else if commandRecord.ActionID = 'n' then begin
			messageAndError := messageStorage.GetMessageByNumber(StrToInt(commandRecord.Data));
			if messageAndError.Error = false then begin
				serialized := messageAndError.Message;
			end else begin
				errorCode := $5306;
				goto sendCode;
			end;
		end else if commandRecord.ActionID = 'i' then begin
			messageAndError := messageStorage.GetMessageByID(commandRecord.Data);
			if messageAndError.Error = false then begin
				serialized := messageAndError.Message;
			end else begin
				errorCode := $5307;
				goto sendCode;
			end;
		end else if commandRecord.ActionID = 'p' then begin
			serialized := messageStorage.Put(userRecord, commandRecord.Data);
		end;
		
		errorCode := $4700 or ord(commandRecord.ActionID[1]);
		fpSend_tc_state(@tcStateSend, connectedSocket, @errorCode, sizeof(errorCode), 0);
		
		serialized := SerializeDataRecords(userRecord) + '|||' + serialized;

		bytes := Length(serialized);
		while bytes > 0 do begin
			if bytes >= CHUNK_SIZE then begin
				buffer := Copy(serialized, Length(serialized) - bytes + 1, CHUNK_SIZE);
				fpSend_tc_state(@tcStateSend, connectedSocket, PUInt8(@buffer)+1, CHUNK_SIZE, 0);		
				bytes := bytes - CHUNK_SIZE;
			end else begin
				buffer := Copy(serialized, Length(serialized) - bytes + 1, bytes);
				fpSend_tc_state(@tcStateSend, connectedSocket, PUInt8(@buffer)+1, bytes, 0);
				bytes := 0
			end;
		end;
	end else begin
		errorCode := $5305;
		goto sendCode;
	end;

	goto finish;
sendCode:
	fpSend_tc_state(@tcStateSend, connectedSocket, @errorCode, sizeof(errorCode), 0);
finish:
	newlnCopy := NEWLN;
	fpSend_tc_state(@tcStateSend, connectedSocket, @newlnCopy, 1, 0);
endThread:
	fpClose(connectedSocket);
	tcStateSend.Free;
	Terminate;
end;

end.
