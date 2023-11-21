public class NetworkPacket {

    public User user {get; }
    public Leave leave {get; }

    public NetworkPacket(User user, Leave leave){
        this.user = user;
        this.leave = leave;
    }

    public static NetworkPacket Deserialize(String packet){
        packet = packet.TrimEnd('\n');
        String[] parts = packet.Split("|||");
        User user = User.Deserialize(parts[1]);
        Leave leave = Leave.Deserialize(parts[2]);
        if (user != null){
            return new NetworkPacket(user, leave);
        } else {
            return null;
        }
    }

    public String Serialize() {
        String res = "0|||";
        res += user.Serialize();
        return res;
    }

    public static String reply(User user, Leave leave) {
        if (leave != null){
            user.AddLeave(leave.Serialize());
        }
        String res = "4|||";
        res += user.Serialize();
        return res;
    }

}
