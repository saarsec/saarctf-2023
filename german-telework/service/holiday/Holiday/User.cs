using System.Security.Cryptography;
using System.Collections;

public class User {
    String firstName;
    String lastName;
    String password;
    String employeeId;
    String jobDesc;
    int holidaysLeft;
    String lastActions;

    public User(String firstName, String lastName, String password, String employeeId, String jobDesc, int holidaysLeft, String lastActions){
        this.firstName = firstName;
        this.lastName = lastName;
        this.password = password;
        this.employeeId = employeeId;
        this.jobDesc = jobDesc;
        this.holidaysLeft = holidaysLeft;
        this.lastActions = lastActions;
    }

    public static User Deserialize(String data){
        String[] parts = data.Split("||");
        List<String> actions = new List<String>();
        String user = "";
        foreach (String action in parts){
            if (action.StartsWith("0")){
                user = action;
            } else {
                actions.Add(action);
            }
        }
        String actionsString = "";
        if (actions.Count > 0) {
            actionsString = String.Join("||", actions);
        }
        parts = user.Split("|");
        String firstName = parts[1];
        String lastName = parts[2];
        String password = parts[3];
        String employeeId = parts[4];
        String jobDesc = parts[5];
        int holidaysLeft = -1;
        try {
            holidaysLeft = Int32.Parse(parts[6]);
        }
        catch (FormatException){
            return null;
        }
        return new User(firstName, lastName, password, employeeId, jobDesc, holidaysLeft, actionsString);
    }

    public String Serialize() {
        String res = "0|";
        res += this.firstName + "|";
        res += this.lastName + "|";
        res += this.password + "|";
        res += this.employeeId + "|";
        res += this.jobDesc + "|";
        res += this.holidaysLeft.ToString();
        if (lastActions != "") {
            res += "||" + this.lastActions;
        }
        return res;
    }

    public bool TakeTimeOff(Leave leave) {
        int time = leave.ComputeTime();
        if ((this.holidaysLeft - time) >= 0) {
            this.holidaysLeft = this.holidaysLeft - time;
            return true;
        } else {
            return false;
        }
    }

    public String CreatePath() {
        SHA256 context = SHA256.Create();
        String complete = this.firstName + this.lastName + this.password;
        byte[] completeBytes =  System.Text.Encoding.Unicode.GetBytes(complete);
        byte[] hash = context.ComputeHash(completeBytes);
        return Convert.ToHexString(hash).ToLower(); 
    }

    public void RemoveLeave(Leave leave){
        this.holidaysLeft += leave.ComputeTime();
    }

    public int GetHolidaysLeft(){
        return this.holidaysLeft;
    }
    
    public void SetHolidaysLeft(int holiday){
        this.holidaysLeft = holiday;
    }

    public void AddLeave(String leave){
        String[] lastActions = this.lastActions.Split("||");
        ArrayList lastActionsUpdated = new ArrayList();
        if (lastActions.Length != 0){
            for (int i = 0; i < lastActions.Length; i++){
                String currentAction = lastActions[i];
                if ((currentAction.Length > 0) && !(currentAction[0] == '2')){
                    lastActionsUpdated.Add(currentAction);
                }
            }
        }
        lastActionsUpdated.Add(leave);
        String [] tmp = (String[]) lastActionsUpdated.ToArray(typeof( string ));
        this.lastActions = String.Join("||", tmp);
    }
}
