unit BoardMessageStorage;

{$mode objfpc}{$H+}

interface

uses
	Classes, Generics.Collections, SysUtils, DateUtils, StrUtils, Math, Types,
	Base64, Character,
	BoardTypes;

type
	TBoardMessage = class
		private
			AuthorFirstName: AnsiString;
			AuthorLastName: AnsiString;
			Text: AnsiString;
		public
			constructor Create(authorUserRecord: TTeleworkUserRecord; _text: AnsiString);
			constructor CreateFromFileEncoded(encoded: AnsiString);
			function FileEncode: AnsiString;
			function NetworkEncode: AnsiString;
	end;

	TBoardMessageStorage = class
		private
			messageIDCache: TStringList;
			lastRefresh: TDateTime;
			csAccessingMessages: TRTLCriticalSection;
			function CheckMessageId(messageID: AnsiString): Boolean;
			procedure RefreshCache;
		public
			constructor Create;
			destructor Destroy; override;
			function Put(authorUserRecord: TTeleworkUserRecord; text: AnsiString): AnsiString;
			function GetCount: SizeInt;
			function GetMessageByID(messageID: AnsiString): TMessageAndError;
			function GetMessageByNumber(messageNumber: SizeInt): TMessageAndError;
	end;
const
	DATA_DIR_PATH: AnsiString = 'data/';
	REFRESH_WAIT_TIME = 10;

implementation

{ TBoardMessage }

constructor TBoardMessage.Create(authorUserRecord: TTeleworkUserRecord; _text: AnsiString);
begin
	AuthorFirstName := authorUserRecord.FirstName;
	AuthorLastName := authorUserRecord.LastName;
	Text := _text;
end;

constructor TBoardMessage.CreateFromFileEncoded(encoded: AnsiString);
var
	parts: TStringDynArray;
begin
	parts := SplitString(encoded, ' ');
	if Length(parts) <> 3 then begin
		AuthorFirstName := 'Error';
		AuthorLastName := 'Error';
		Text := 'Error';
		Exit;
	end;
	try
		AuthorFirstName := DecodeStringBase64(parts[0], true);
		AuthorLastName := DecodeStringBase64(parts[1], true);
		Text := DecodeStringBase64(parts[2], true);
	except
		AuthorFirstName := 'Error2';
		AuthorLastName := 'Error2';
		Text := 'Error2';
	end;
end;

function TBoardMessage.FileEncode: AnsiString;
begin
	Result := EncodeStringBase64(AuthorFirstName) + ' ';
	Result := Result + EncodeStringBase64(AuthorLastName) + ' ';
	Result := Result + EncodeStringBase64(Text);
end;

function TBoardMessage.NetworkEncode: AnsiString;
begin
	Result := AuthorFirstName + '|';
	Result := Result + AuthorLastName + '|';
	Result := Result + Text;
end;

{ TBoardMessageStorage }

constructor TBoardMessageStorage.Create;
begin
	messageIDCache := TStringList.Create;
	messageIDCache.Sorted := true;
	if DirectoryExists(DATA_DIR_PATH) = false then begin
		MkDir(DATA_DIR_PATH);
	end;
	InitCriticalSection(csAccessingMessages);
end;

destructor TBoardMessageStorage.Destroy;
begin
	messageIDCache.Free;
	DoneCriticalSection(csAccessingMessages);
	inherited;
end;

function TBoardMessageStorage.CheckMessageId(messageID: AnsiString): Boolean;
var
	C: Char;
begin
	for C in messageID do begin
		if not (IsNumber(C) or (C = 'A') or (C = 'B') or (C = 'C') or (C = 'D') or (C = 'E') or (C = 'F') or (C = '-')) then begin
			Result := false;
			Exit;
		end;
	end;
	Result := true;
end;

procedure TBoardMessageStorage.RefreshCache;
var
	messageID: AnsiString;
	searchRec: TSearchRec;
begin
	if CompareDateTime(IncSecond(lastRefresh, REFRESH_WAIT_TIME), Now) = LessThanValue then begin
		messageIDCache.Clear;
		if FindFirst(DATA_DIR_PATH + '*.msg', faAnyFile, searchRec) = 0 then begin
			repeat
				if searchRec.Attr <> faDirectory then begin
					messageID := searchRec.Name;
					if (Length(messageID) > 4) then begin
						SetLength(messageID, Length(messageID) - 4);
					end;
					messageIDCache.Add(messageID)
				end;
			Until FindNext(searchRec) <> 0;
			FindClose(searchRec);
		end;
		lastRefresh := Now;
	end;
end;

function TBoardMessageStorage.Put(authorUserRecord: TTeleworkUserRecord; text: AnsiString): AnsiString;
var
	message: TBoardMessage;
	messageFileEncoded: AnsiString;
	messageID: AnsiString;
	fileGUID: TGUID;
	fileStream: TFileStream;
begin
	EnterCriticalSection(csAccessingMessages);
	message := TBoardMessage.Create(authorUserRecord, text);
	
	messageFileEncoded := message.FileEncode();
	
	CreateGUID(fileGUID);
	messageID := GUIDToString(fileGUID);
	Delete(messageID, 1, 1);
	SetLength(messageID, Length(messageID) - 1);
	messageID := IntToStr(DateTimeToUnix(Now)) + '-' + messageID;

	fileStream := TFileStream.Create(
		DATA_DIR_PATH + messageID + '.msg',
		fmCreate
	);
	try
		fileStream.WriteBuffer(Pointer(messageFileEncoded)^, Length(messageFileEncoded));
	finally
		fileStream.Free;
	end;
	message.Free;

	messageIDCache.Add(messageID);
	
	LeaveCriticalSection(csAccessingMessages);
	
	Result := messageID;
end;

function TBoardMessageStorage.GetCount: SizeInt;
begin
	EnterCriticalSection(csAccessingMessages);
	refreshCache;
	Result := messageIDCache.Count;
	LeaveCriticalSection(csAccessingMessages);
end;

function TBoardMessageStorage.GetMessageByID(messageID: AnsiString): TMessageAndError;
var
	messageFileName: AnsiString;
	messageFileEncoded: AnsiString;
	message: TBoardMessage;
	fileStream: TFileStream;
begin
	EnterCriticalSection(csAccessingMessages);
	refreshCache;

	Result.Error := true;

	if CheckMessageId(messageID) = false then begin
		Result.Message := '';
		LeaveCriticalSection(csAccessingMessages);
		Exit;
	end;
	messageFileName := messageID + '.msg';

	if FileExists(DATA_DIR_PATH + messageFileName) = false then begin
		Result.Message := '';
		LeaveCriticalSection(csAccessingMessages);
		Exit;
	end;

	fileStream := TFileStream.Create(DATA_DIR_PATH + messageFileName, fmOpenRead);
	try
		SetLength(messageFileEncoded, fileStream.Size);
		fileStream.Read(Pointer(messageFileEncoded)^, Length(messageFileEncoded));
	finally
		fileStream.Free;
	end;

	message := TBoardMessage.CreateFromFileEncoded(messageFileEncoded);
	Result.Message := message.NetworkEncode;
	message.Free;

	Result.Error := false;
	LeaveCriticalSection(csAccessingMessages);
end;

function TBoardMessageStorage.GetMessageByNumber(messageNumber: SizeInt): TMessageAndError;
begin
	EnterCriticalSection(csAccessingMessages);
	refreshCache;

	if ((messageNumber >= 0) and (messageNumber < messageIDCache.Count)) then begin
		Result := GetMessageByID(messageIDCache[messageNumber]);
	end else begin
		Result.Message := '';
		Result.Error := true;
	end;

	LeaveCriticalSection(csAccessingMessages);
end;

end.
