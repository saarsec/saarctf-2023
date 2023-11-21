public class Task {
    String id;
    String requestType;
    String name;
    String description;
    String stepsRepr;
    String epic;
    String sprint;
    int hoursEstimated;

    public Task(String id, String requestType, String name, String description, String stepsRepr, String epic, String sprint, int hoursEstimated){
        this.id = id;
        this.requestType = requestType;
        this.name = name;
        this.description = description;
        this.stepsRepr = stepsRepr;
        this.epic = epic;
        this.sprint = sprint;
        this.hoursEstimated = hoursEstimated;
    }

    public static Task deserialize(String serialized)throws PacketFormatException {
        String[] parts = serialized.split("\\|");
        int packetId = Integer.parseInt(parts[0]);
        if (packetId != 1) {
            throw new PacketFormatException("Malformed task packet!");
        }
        String requestType = parts[1];
        String name = parts[2];
        String description = parts[3];
        String stepsRepr = parts[4];
        String epic = parts[5];
        String sprint = parts[6];
        int hoursEstimated = Integer.parseInt(parts[7]);
        return new Task(parts[0], requestType, name, description, stepsRepr, epic, sprint, hoursEstimated);
    }

    public String serialize() {
        String res = "";
        res += this.id + "|";
        res += this.requestType + "|";
        res += this.name + "|";
        res += this.description + "|";
        res += this.stepsRepr + "|";
        res += this.epic + "|";
        res += this.sprint + "|";
        res += Integer.toString(this.hoursEstimated);
        res += "\n";
        return res;
    }

    public String getRequestType(){
        return this.requestType;
    }

    public String getDescription(){
        return this.description;
    }

    public String getName(){
        return this.name;
    }
    
    public String getEpic(){
        return this.epic;
    }

    public Task setError() {
        this.requestType = "99";
        return this;
    }

    public Task setTaskDetails() {
        this.requestType = "2";
        return this;
    }

}
