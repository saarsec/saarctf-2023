using System;
using System.Globalization;


public class Leave {
    public String id;
    public String requestType {get; set;}
    public DateTime start {get; }
    public DateTime end {get; }
    String reason;
    String destination;
    String phone;


    public Leave(String id, String requestType, DateTime start, DateTime end, String reason, String destination, String phone){
        this.id = id;
        this.requestType = requestType;
        this.start = start;
        this.end = end;
        this.reason = reason;
        this.destination = destination;
        this.phone = phone;
    }

    public static Leave Deserialize (String data) {
        String[] parts = data.Split("|");
        String id = parts[0];
        String requestType = parts[1];
        CultureInfo c = new CultureInfo("de-DE");
        DateTime start = new DateTime(1900, 1, 1);
        DateTime end = new DateTime(1900, 1, 1);

        try{
            start = DateTime.Parse(parts[2], c);
            end = DateTime.Parse(parts[3], c);
        } catch (FormatException){
            return null;
        }
        if (start == null || end == null)
            return null;
        String reason = parts[4];
        String destination = parts[5];
        String phone = parts[6];
        return new Leave(id, requestType, start, end, reason, destination, phone); 
    }

    public String Serialize() {
        String serialized = "";
        serialized += id.ToString() + "|";
        serialized += requestType.ToString() + "|";
        CultureInfo c = new CultureInfo("de-DE");
        serialized += start.ToString(c) + "|";
        serialized += end.ToString(c) + "|";
        serialized += reason.ToString() + "|";
        serialized += destination.ToString() + "|";
        serialized += phone.ToString();
        return serialized;
    }

    public static String SerializeList(List<Leave> leaveList) {
        if (leaveList.Count == 0)
            return "";
        String serialized = "";
        foreach (Leave l in leaveList){
            serialized += l.Serialize() + "||";
        }
        return serialized.Remove(serialized.Length - 2);
    }

    public int ComputeTime () {
        return (this.end - this.start).Days;
    }
}
