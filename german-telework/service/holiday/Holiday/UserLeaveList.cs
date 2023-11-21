using System.IO;
using System.Text;

public class UserLeaveList {
    User user;
    List<Leave> leaveList = new List<Leave>();
    
    public UserLeaveList (User user) {
        this.user = user;
        String userPath = "data/" + this.user.CreatePath();
        if (!Directory.Exists(userPath)){
            return;
        }
        StreamReader sr;
        try {
            sr = new StreamReader(userPath + "/ser.txt", new UnicodeEncoding(), false);
        } catch (FileNotFoundException f){
            return;
        }
        String tmp = sr.ReadToEnd();
        tmp = tmp.TrimEnd('\n');
        String data = "";
        foreach(byte b in tmp){
            data += Convert.ToChar(b);
        }
        if (data.Length == 0){
            return;
        }
        String[] lrs = data.Split("\n");
        int holidaySpent = 0;
        foreach (String l in lrs) {
            Leave leave = Leave.Deserialize(l);
            if (leave != null){
                leaveList.Add(leave);
                holidaySpent += leave.ComputeTime();
            }
        }
        int userHolidaySpent = user.GetHolidaysLeft();
        if ((30-holidaySpent) != userHolidaySpent){
            user.SetHolidaysLeft(30-holidaySpent);
        }

    }

    public bool TakeTimeOff(Leave leave) {
        foreach (Leave l in this.leaveList) {
            if ( ((l.start <= leave.start) && (l.end >= leave.start)) || ((l.start < leave.end) && (l.end > leave.end)) ) {
                return false;
            }
        }
        if (user.TakeTimeOff(leave) && leave.start > DateTime.Now && leave.end > DateTime.Now){
            this.leaveList.Add(leave);
            return true;
        }
        return false;
    }


    public Leave CancelLeave(Leave leave){
        foreach (Leave l in leaveList) {
            if ((l.start == leave.start) && (l.end == leave.end)) {
                user.RemoveLeave(l);
                leaveList.Remove(l);
                return l;
            }
        }
        return null;
    }


    public void Store(){
        String userPath = "data/" + this.user.CreatePath();
        if ((this.leaveList.Count == 0) && (Directory.Exists(userPath))){
            Directory.Delete(userPath,true);
            return;
        }
        Directory.CreateDirectory(userPath);
        String serialized = "";
        foreach (Leave l in this.leaveList) {
            serialized += l.Serialize() + "\n";
        }
        System.IO.File.WriteAllText(userPath + "/ser.txt", serialized, new UnicodeEncoding());
    }

    public String Serialize(){
        return Leave.SerializeList(this.leaveList);
    }
}
