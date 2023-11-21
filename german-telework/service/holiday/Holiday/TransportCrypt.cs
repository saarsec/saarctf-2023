public class TransportCrypt {

    ulong InitialSeed = 0xEA0A8EEA0A8EEA0A;
    ulong Mask = 0xffffffffffffffff;

    ulong Seed;
    byte Count;

    public TransportCrypt(){
        this.Seed = InitialSeed;
        this.Count = 0;
    }

    private ulong TransportCryptKeystream(ulong seed){
        ulong result = seed;
        result ^= result << 13 & Mask;
        result ^= result >> 7 & Mask;
        result ^= result << 17 & Mask;
        return result & Mask;
    }

    private byte GetKeyByte(){
        if (this.Count == 16){
            this.Count = 0;
            this.Seed = this.TransportCryptKeystream(this.Seed);
        }
        byte result = (byte) ((this.Seed >> this.Count) & 0xff);
        this.Count += 1;
        return result;
    }

    private byte[] TransportCryptState(byte[] buffer){
        List<Byte> tmp = new List<Byte>();
        foreach (byte b in buffer) {
            byte keyByte = this.GetKeyByte();
            tmp.Add((byte) (b ^ keyByte));
        }
        byte[] res = tmp.ToArray();
        return res;
    }

    public static byte[] CryptoBuffer(byte[] buffer) {
        TransportCrypt tc = new TransportCrypt();
        return tc.TransportCryptState(buffer);
    }
}
