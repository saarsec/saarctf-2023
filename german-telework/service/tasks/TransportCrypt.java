import java.util.*;


public class TransportCrypt {

    long initialSeed = 0xEA0A8EEA0A8EEA0AL;
    long mask = 0xffffffffffffffffL;

    long seed;
    byte count;

    public TransportCrypt(){
        this.seed = initialSeed;
        this.count = 0;
    }

    private long transportCryptKeystream(long seed){
        long result = seed;
        result ^= result << 13 & mask;
        result ^= result >>> 7 & mask;
        result ^= result << 17 & mask;
        return result & mask;
    }

    private byte getKeyByte(){
        if (this.count == 16){
            this.count = 0;
            this.seed = this.transportCryptKeystream(this.seed);
        }
        byte result = (byte) ((this.seed >> this.count) & 0xff);
        this.count += 1;
        return result;
    }

    private byte[] transportCryptState(byte[] buffer){
        List<Byte> tmp = new ArrayList<Byte>();
        for (byte b : buffer) {
            byte keyByte = this.getKeyByte();
            tmp.add((byte) (b ^ keyByte));
        }
        byte[] res = new byte[tmp.size()];
        for (int i = 0; i<tmp.size(); i++)
            res[i] = tmp.get(i);
        return res;
    }

    public static byte[] cryptoBuffer(byte[] buffer) {
        TransportCrypt tc = new TransportCrypt();
        return tc.transportCryptState(buffer);
    }
}
