import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.io.UnsupportedEncodingException;
import java.nio.charset.StandardCharsets;
import java.util.*;



public class User {
    String firstName;
    String lastName;
    String password;
    String employeeId;
    String jobDescription;
    int holidaysLeft;
    String lastActions;

    public User(String firstName, String lastName, String password, String employeeId, String jobDescription, int holidaysLeft, String lastActions){
        this.firstName = firstName;
        this.lastName = lastName;
        this.password = password;
        this.employeeId = employeeId;
        this.jobDescription = jobDescription;
        this.holidaysLeft = holidaysLeft;
        this.lastActions = lastActions;
    }

    public String serialize(){
        String res = "0|";
        res += this.firstName + "|";
        res += this.lastName + "|";
        res += this.password + "|";
        res += this.employeeId + "|";
        res += this.jobDescription + "|";
        res += this.holidaysLeft + "||";
        res += this.lastActions;
        return res;
    }

    public static User deserialize(String serialized) throws PacketFormatException {
        String[] objects = serialized.split("\\|\\|");
        String user = "";
        List<String> lastActionsList = new ArrayList<String>();
        for (String entry : objects){
            if (entry.startsWith("0")) {
                user = entry;
            } else {
                lastActionsList.add(entry);
            }
        }
        String lastActions = "";
        if (lastActionsList.size() > 0){
            lastActions = String.join("||", lastActionsList);
        }
        String[] parts = user.split("\\|");
        int id = Integer.parseInt(parts[0]);
        if (id != 0){
            throw new PacketFormatException("Wrong user format!"); 
        }
        String firstName = parts[1];
        String lastName = parts[2];
        String password = parts[3];
        String employeeId = parts[4];
        String jobDescription = parts[5];
        int holidaysLeft = Integer.parseInt(parts[6]);
        return new User(firstName, lastName, password, employeeId, jobDescription, holidaysLeft, lastActions);
    }

    private static final byte[] HEX_ARRAY = "0123456789ABCDEF".getBytes(StandardCharsets.US_ASCII);

    private static String bytesToHex(byte[] bytes) {
        byte[] hexChars = new byte[bytes.length * 2];
        for (int j = 0; j < bytes.length; j++) {
            int v = bytes[j] & 0xFF;
            hexChars[j * 2] = HEX_ARRAY[v >>> 4];
            hexChars[j * 2 + 1] = HEX_ARRAY[v & 0x0F];
        }
        return new String(hexChars, StandardCharsets.UTF_8);
    }

    public String createPath() throws UnsupportedEncodingException {
        MessageDigest md;
        try {
            md = MessageDigest.getInstance("SHA-256");
        } catch (NoSuchAlgorithmException e) {
            System.err.println("No security provider found for sha256");
            return null;
        }
        String complete = this.firstName;
        byte[] ser = complete.getBytes("UTF-8");
        md.update(ser);
        byte [] digest = md.digest();
        String res = User.bytesToHex(digest).toLowerCase();
        return res;
    }

    public String getLastActions(){
        return this.lastActions;
    }

    public void addTask(String task){
        String[] lastActions = this.lastActions.split("\\|\\|");
        List<String> lastActionsUpdated = new ArrayList<String>();
        if (lastActions.length != 0) {
            for (int i = 0; i < lastActions.length; i++){
                String currentAction = lastActions[i];
                if ((currentAction.length() > 0) && !(currentAction.charAt(0) == '1')){
                    lastActionsUpdated.add(currentAction);
                }
            }
        }
        lastActionsUpdated.add(task);
        this.lastActions = String.join("||", lastActionsUpdated);
    }


}
