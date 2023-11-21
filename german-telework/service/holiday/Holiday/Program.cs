using System;
using System.Net;
using System.Net.Sockets;
using System.Text;

public class SocketListener
{
    public static int Main(String[] args)
    {
        StartServer();
        return 0;
    }


    public static void StartServer()
    {
        IPAddress ipAddress = IPAddress.Parse("127.0.0.1"); 
        IPEndPoint localEndPoint = new IPEndPoint(ipAddress, 30003);
        Socket listener = new Socket(ipAddress.AddressFamily, SocketType.Stream, ProtocolType.Tcp);
        listener.Bind(localEndPoint);
        listener.Listen(10);
        while(true){
            try {
                Socket handler = listener.Accept();
                Thread clientThread = new Thread(new ParameterizedThreadStart(HandleClientCommunication));
                clientThread.Start((object)handler);
            }
            catch (Exception e)
            {
                Console.WriteLine("Error: " + e.ToString());
            }
        }
    }

    private static void HandleClientCommunication(object Client)
    {
        Socket sock = (Socket)Client;
        String data = null;
        byte[] bytes = null;

        bytes = new byte[1024];
        int bytesRec = sock.Receive(bytes);
        Array.Resize(ref bytes, bytesRec);
        bytes = TransportCrypt.CryptoBuffer(bytes);
        data = Encoding.UTF8.GetString(bytes, 0, bytesRec).TrimEnd('\n');
        NetworkPacket np = NetworkPacket.Deserialize(data);
        UserLeaveList ull = new UserLeaveList(np.user);
        Leave leaveRequest = np.leave;
        User user = np.user;
        bool success = false;
        String reply = "";
        if (leaveRequest == null){
            reply = NetworkPacket.reply(user, leaveRequest);
            byte[] error = Encoding.UTF8.GetBytes(reply + "\n");
            sock.Send(TransportCrypt.CryptoBuffer(error));
            sock.Shutdown(SocketShutdown.Both);
            sock.Close();
            return;
        }
        switch (leaveRequest.requestType) {
            case "0":
            success = ull.TakeTimeOff(leaveRequest);
            if (!success){
                leaveRequest.requestType = "99";
            }
            ull.Store();
            reply = NetworkPacket.reply(user, leaveRequest);
            break;
            case "1":
            Leave removed = ull.CancelLeave(leaveRequest);
            if (removed == null){
                leaveRequest.requestType = "99";
            } 
            ull.Store();
            if (removed != null){
                reply = NetworkPacket.reply(user, removed);
            } else {
                reply = NetworkPacket.reply(user, leaveRequest);
            }
            break;
            case "2":
            reply = NetworkPacket.reply(user, leaveRequest);
            reply += " |||" + ull.Serialize();
            break;
            default:
            break;
        }
        byte[] msg = Encoding.UTF8.GetBytes(reply + "\n");
        sock.Send(TransportCrypt.CryptoBuffer(msg));
        sock.Shutdown(SocketShutdown.Both);
        sock.Close();
    }
}
