unit TransportCrypt;

{$mode objfpc}{$H+}

interface

uses
	Classes, SysUtils, Sockets, ctypes, UnixType;

type
	TTransportCryptState = class
		public
			Seed: UInt64;
			Count: UInt8;
			constructor Create;
	end;
	PTTransportCryptState = ^TTransportCryptState;
	function fpRecv_tc_state(state: PTTransportCryptState; s: cint; buf: pointer; len: size_t; flags: cint): ssize_t;
	function fpRecv_tc(s: cint; buf: pointer; len: size_t; flags: cint): ssize_t;
	function fpSend_tc_state(state: PTTransportCryptState; s: cint; msg: pointer; len: size_t; flags: cint): ssize_t;
	function fpSend_tc(s: cint; msg: pointer; len: size_t; flags: cint): ssize_t;
const
	TRANSPORT_CRYPT_INITIAL_SEED: UInt64 = UInt64($EA0A8EEA0A8EEA0A);

implementation

{ TTransportCryptState }

constructor TTransportCryptState.Create;
begin
	Seed := TRANSPORT_CRYPT_INITIAL_SEED;
	Count := 0;
end;

{ Global Functions }

function TransportCryptKeystream(seed: UInt64): UInt64;
begin
	Result := seed;
	Result := Result xor (Result << 13);
	Result := Result xor (Result >> 7);
	Result := Result xor (Result << 17);
end;

function TransportCryptGetKeyByte(state: PTTransportCryptState): UInt8;
begin
	if state^.Count = 16 then begin
		state^.Count := 0;
		state^.Seed := TransportCryptKeystream(state^.Seed);
	end; 
	Result := (state^.Seed >> state^.Count);
	state^.Count := state^.Count + 1;
end;

procedure TransportCryptState(state: PTTransportCryptState; buf: pointer; len: size_t);
var
	i: size_t;
begin
	for i := 0 to len - 1 do begin
		(PUInt8(buf)+i)^ := PUInt8(buf+i)^ xor TransportCryptGetKeyByte(state);
	end;
end;

function fpRecv_tc_state(state: PTTransportCryptState; s: cint; buf: pointer; len: size_t; flags: cint): ssize_t;
begin
	Result := fpRecv(s, buf, len, flags);
	if Result > 0 then begin
		TransportCryptState(state, buf, Result);
	end;
end;

function fpRecv_tc(s: cint; buf: pointer; len: size_t; flags: cint): ssize_t;
var
	state: TTransportCryptState;
begin
	state := TTransportCryptState.Create;
	Result := fpRecv_tc_state(@state, s, buf, len, flags);
	state.Free;
end;

function fpSend_tc_state(state: PTTransportCryptState; s: cint; msg: pointer; len: size_t; flags: cint): ssize_t;
begin
	TransportCryptState(state, msg, len);
	Result := fpSend(s, msg, len, flags);
end;

function fpSend_tc(s: cint; msg: pointer; len: size_t; flags: cint): ssize_t;
var
	state: TTransportCryptState;
begin
	state := TTransportCryptState.Create;
	Result := fpSend_tc_state(@state, s, msg, len, flags);
	state.Free;
end;

end.
