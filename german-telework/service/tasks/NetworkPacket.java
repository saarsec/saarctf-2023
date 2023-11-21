public class NetworkPacket {

    User user;
    Task task;

    public NetworkPacket (User user, Task task) {
        this.user = user;
        this.task = task;
    }

    public static NetworkPacket deserialize (String data) throws WrongTargetException, PacketFormatException {
        String[] parts = data.split("\\|\\|\\|");
        if (!(parts[0].equals("0"))){
            throw new WrongTargetException("This packet is not for me!");
        }
        String user_ser = parts[1];
        String task_ser = parts[2];
        User user = User.deserialize(user_ser);
        Task task = Task.deserialize(task_ser);
        return new NetworkPacket(user, task);
    }

    public User getUser(){
        return this.user;
    }

    public Task getTask(){
        return this.task;
    }

    public static String reply(User user, Task task){
        user.addTask(task.serialize());
        String res = "4|||";
        res += user.serialize();
        return res.strip();
    }
}
