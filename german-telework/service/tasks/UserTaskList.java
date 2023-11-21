import java.util.List;
import java.util.ArrayList;
import java.util.Iterator;
import java.io.UnsupportedEncodingException;
import java.io.File;
import java.io.IOException;
import java.io.BufferedWriter;
import java.io.BufferedReader;
import java.io.FileWriter;
import java.io.FileReader;
import java.nio.charset.Charset;

public class UserTaskList {
    User user;
    List<Task> taskList = new ArrayList<>();

    public UserTaskList(User user){
        String userpath = null;
        try {
            userpath = user.createPath();
        } catch (UnsupportedEncodingException e){
            System.err.println("user contains non-utf8 content!");
        }
        if (userpath == null){
            return;
        }
        File f = new File("data/" + userpath + "/ser.txt");
        Charset charset = Charset.forName("US-ASCII");
        try (BufferedReader reader = new BufferedReader (new FileReader(f))) {
            String line = reader.readLine();

			while (line != null) {
                Task task = null;
                try {
                    task = Task.deserialize(line);
                } catch (PacketFormatException e) {
                    System.err.println("Malformed userdata!");
                }
                if (task != null) {
                    this.taskList.add(task);
                }
				line = reader.readLine();
			}
        } catch (IOException x) {
            System.err.println(x.getMessage());
        }
        this.user=user;
    }

    public void addTask (Task task) throws TaskAlreadyExistsException {
        for (Task t : taskList) {
            if (t.getName().equals(task.getName())){
                throw new TaskAlreadyExistsException("Task already exists!");
            }
        } 
        taskList.add(task);
    }

    public List<Task> getAllTasks () throws TaskDoesNotExistException {
        return this.taskList;
    }
    
    public void removeTask (Task task) throws TaskDoesNotExistException {
        Iterator<Task> iter = taskList.iterator();
        while (iter.hasNext()) {
            Task item = iter.next();
            if (item.getName().equals(task.getName()) && item.getEpic().equals(task.getEpic())){
                iter.remove();
                return;
            }
        }
        throw new TaskDoesNotExistException("Task does not exist!");
    }

    public void store(){
        String userpath = null;
        try {
            userpath = user.createPath();
        } catch (UnsupportedEncodingException e){
            System.err.println("user contains non-utf8 content!");
        }
        if (userpath == null){
            return;
        }
        File theDir = new File("data/" + userpath);
        if (!theDir.exists()){
            theDir.mkdirs();
        }
        StringBuilder sb = new StringBuilder();
        for (Task task : taskList) {
            sb.append(task.serialize());
        }
        String s = sb.toString();
        File f = new File("data/" + userpath + "/ser.txt");
        Charset charset = Charset.forName("US-ASCII");
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(f))) {
            writer.write(s, 0, s.length());
        } catch (IOException x) {
            System.err.format("IOException: %s%n", x);
        }
    }
}
