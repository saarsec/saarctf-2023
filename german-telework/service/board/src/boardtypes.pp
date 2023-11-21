unit BoardTypes;

{$mode objfpc}{$H+}

interface

type
	TEmployeeID = AnsiString;
	
	TTeleworkUserRecord = record
		FirstName: AnsiString;
		LastName: AnsiString;
		Password: AnsiString;
		EmployeeID: TEmployeeID;
		JobDesc: AnsiString;
		HolidaysLeft: UInt32;
		Remainder: AnsiString;
		Error: Boolean;
	end;
	
	TCommandRecord = record
		ActionID: AnsiString;
		Data: AnsiString;
		Error: Boolean;
	end;

	TMessageAndError = record
		message: AnsiString;
		Error: Boolean;
	end;

implementation

end.