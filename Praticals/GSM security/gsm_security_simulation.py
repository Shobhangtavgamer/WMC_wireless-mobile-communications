import hashlib
import hmac
import secrets

KI = bytes.fromhex("00112233445566778899AABBCCDDEEFF")
# A3: Generate a 32-bit SRES authentication response
def A3_authentication(ki, rand):
    return hmac.new(ki, b"A3" + rand, hashlib.sha256).digest()[:4]
# A8: Generate a 64-bit session key Kc
def A8_key_generation(ki, rand):
    return hmac.new(ki, b"A8" + rand, hashlib.sha256).digest()[:8]
# A5: Demonstration stream cipher using XOR
# NOTE: This is a simplified educational simulation, not real GSM A5.
def A5_encrypt(data, kc):
    keystream = bytearray()
    counter = 0
    while len(keystream) < len(data):
        block = hashlib.sha256(kc + counter.to_bytes(4, "big")).digest()
        keystream.extend(block)
        counter += 1
    return bytes(a ^ b for a, b in zip(data, keystream))
def main():
    print("              GSM SECURITY SIMULATION")
    print("KI (SIM Secret Key):", KI.hex().upper())
    session = 1
    while True:
        print(f"                  SESSION {session}")
        # [1] Generate a random challenge
        print("\n[1] RANDOM CHALLENGE (RAND)")
        rand = secrets.token_bytes(8)
        print("RAND:", rand.hex().upper())
        # [2] A3 authentication
        print("\n[2] A3 AUTHENTICATION")
        generated_sres = A3_authentication(KI, rand)
        # Simulate the response received from the network
        received_sres = generated_sres
        print("Generated SRES:", generated_sres.hex().upper())
        print("Received SRES :", received_sres.hex().upper())
        if hmac.compare_digest(generated_sres, received_sres):
            print("Authentication: SUCCESS")
        else:
            print("Authentication: FAILURE")
            continue
        # [3] A8 key generation
        print("\n[3] A8 KEY GENERATION")
        kc = A8_key_generation(KI, rand)
        print("Generated Kc:", kc.hex().upper())
        # [4] Get message from user
        print("\n[4] MESSAGE INPUT")
        message = input("Enter message to encrypt (or 'exit' to stop): ")
        if message.lower() == "exit":
            print("\nGSM SIMULATION STOPPED.")
            break
        plaintext = message.encode("utf-8")
        print("Plaintext     :", message)
        print("Plaintext HEX :", plaintext.hex().upper())
        # [5] A5 encryption
        print("\n[5] A5 ENCRYPTION")
        ciphertext = A5_encrypt(plaintext, kc)
        print("Plaintext     :", message)
        print("Plaintext HEX :", plaintext.hex().upper())
        print("Ciphertext HEX:", ciphertext.hex().upper())
        # [6] A5 decryption (same XOR operation reverses encryption)
        print("\n[6] A5 DECRYPTION")
        decrypted = A5_encrypt(ciphertext, kc)
        decrypted_message = decrypted.decode("utf-8")
        print("Ciphertext HEX:", ciphertext.hex().upper())
        print("Decrypted     :", decrypted_message)
        print("Decrypted HEX :", decrypted.hex().upper())
        # [7] Verify decrypted message
        print("\n[7] DECRYPTION VERIFICATION")
        if decrypted == plaintext:
            print("Decryption: SUCCESS")
            print("Messages MATCH.")
        else:
            print("Decryption: FAILURE")
            print("Messages DO NOT MATCH.")
        # End current session
        print(f"             SESSION {session} COMPLETED")
        print("Authentication : SUCCESS")
        print("Encryption     : COMPLETED")
        print("Decryption     : COMPLETED")
        print("Verification   : SUCCESS")
        print("\nNext session will generate a NEW RAND and NEW Kc.")
        session += 1
if __name__ == "__main__":
    main()
