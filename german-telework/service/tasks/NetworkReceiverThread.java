import java.net.Socket;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.DataInputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.lang.NumberFormatException;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.ArrayList;


public class NetworkReceiverThread extends Thread {
    protected Socket socket;

    public NetworkReceiverThread(Socket clientSocket) {
        this.socket = clientSocket;
    }

    public void run() {
        InputStream inp = null;
        DataOutputStream out = null;
        DataInputStream inStream = null;
        try {
            inp = socket.getInputStream();
            inStream = new DataInputStream(inp);
            out = new DataOutputStream(socket.getOutputStream());
        } catch (IOException e) {
            return;
        }
        byte[] rawInput = new byte[1024];
        try {
            int numRead = inStream.read(rawInput, 0, 1024);
            byte[] actual = new byte[numRead];
            System.arraycopy(rawInput, 0, actual, 0, numRead);
            actual = TransportCrypt.cryptoBuffer(actual);
            String line = new String(actual, StandardCharsets.UTF_8);
            line = line.trim();
            UserTaskList utl = null;
            if (line == null)  {
                socket.close();
                return;
            } else {
                NetworkPacket networkPacket;
                try{
                    networkPacket = NetworkPacket.deserialize(line);
                } catch (WrongTargetException e){
                    System.err.println("WrongTargetException: " + e.getMessage() + "\n");
                    return;
                } catch (NumberFormatException e){
                    System.err.println("NumberFormatException: " + e.getMessage() + "\n");
                    return;
                } catch (PacketFormatException e){
                    System.err.println("PacketFormatException: " + e.getMessage() + "\n");
                    return;
                }
                Task task = networkPacket.getTask();
                User user = networkPacket.getUser();
                if (utl == null) {
                    utl = new UserTaskList(user);
                }
                String reply = null;
                Task reply_task = null;
                byte[] encodedReply = null;
                byte[] encryptedReply = null;
                switch (task.getRequestType()) {
                    case "0":
                        try {
                            utl.addTask(task);
                        } catch (TaskAlreadyExistsException e){
                            task = task.setError();
                        }
                        utl.store();
                        reply = NetworkPacket.reply(user, task) + "\n";
                        encodedReply = StandardCharsets.UTF_8.encode(reply).array();
                        encryptedReply = TransportCrypt.cryptoBuffer(encodedReply);
                        out.write(encryptedReply, 0, encryptedReply.length);
                        break;

                    case "1":
                        try{
                            utl.removeTask(task);
                        } catch (TaskDoesNotExistException e){
                            task = task.setError();
                        }
                        utl.store();
                        reply = NetworkPacket.reply(user, task) + "\n";
                        encodedReply = StandardCharsets.UTF_8.encode(reply).array();
                        encryptedReply = TransportCrypt.cryptoBuffer(encodedReply);
                        out.write(encryptedReply, 0, encryptedReply.length);
                        break;

                    case "2":
                        try{
                            List<Task> allTasks = utl.getAllTasks();
                            List<String> allTasksSerialized = new ArrayList<String>();
                            allTasks.forEach( (t) -> allTasksSerialized.add(t.serialize().replace("\n","")) );
                            reply = NetworkPacket.reply(user, task) + "|||" + String.join("||", allTasksSerialized) + "\n";
                            encodedReply = StandardCharsets.UTF_8.encode(reply).array();
                            encryptedReply = TransportCrypt.cryptoBuffer(encodedReply);
                            out.write(encryptedReply, 0, encryptedReply.length);
                        } catch (TaskDoesNotExistException e){
                            task = task.setError();
                            reply = NetworkPacket.reply(user, task) + "\n";
                            encodedReply = StandardCharsets.UTF_8.encode(reply).array();
                            encryptedReply = TransportCrypt.cryptoBuffer(encodedReply);
                            out.write(encryptedReply, 0, encryptedReply.length);
                        }
                        break;

                    default:
                        break;
                }
            }
        } catch (IOException e) {
            e.printStackTrace();
            return;
        }
    }
}

