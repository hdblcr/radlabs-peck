# install HTTP protocol packages
import requests
import codecs
import base64

# set requests constants
url = "http://localhost:3000/"


# clean hex
def cleanHex(rawHex):
    '''
    cleanHex takes a raw input hexadecimal and removes extraneous characters to
    return a strictly hexadecimal result.
    '''
    print(rawHex, "<- hex, type of hex ->", type(rawHex))
    hex = str(rawHex)
    print(hex, "<- hex, type of hex ->", type(hex))
    if hex[0] == ':':
        hex = hex[1:]
    if hex[-1] == '\n':
        hex = hex[:-1]
    hex = str.encode(hex)
    print(hex, "<- hex, type of hex ->", type(hex))
    return hex


# convert a line of hex to a line of base64
def hex2b64(hex):
    '''
    This function simplifies transitioning from a line of hex to the base64
    equivalent.
    '''
    hexBytes = cleanHex(hex)
    print(hexBytes, "<- hex, type of hex ->", type(hexBytes))
    # a = codecs.decode(hexBytes, 'hex')
    b = codecs.encode(hexBytes, 'base64')
    c = b.decode()
    return c[:-1]


# # Convert base 64 to hexadecimal for checksum calculations
def b64toValue(b64):
    '''
    Takes a chunk in b64 and returns that value in decimal form.
    '''
    if b64[-1] == '\n':
        b64 = b64[:-1]
    b64 = str.encode(b64)
    hex = codecs.encode(b64, 'hex')
    return int(hex, 16)


# send the chunk
def sendChunk(b64):
    '''
    sendChunk posts the base64-encoded chunk of data to the device. It returns
    the response from the device.
    '''
    str2send = "CHUNK: " + b64
    return requests.post(url, str2send)


# request the checksum
def requestChecksum():
    '''
    requestChecksum sends a checksum request to the device and returns the
    device response.
    '''
    checksumRequest = "CHECKSUM"
    checksumResponse = requests.post(url, checksumRequest)
    # print(checksumResponse.text)
    return checksumResponse.text


# calculate checksum of chunk
def calcChunkChecksum222(hex):
    '''
    calcChunkChecksum takes the data chunk in hexadecimal, and determines how
    much the additional chunk of data would add to the full checksum. It returns
    that value.
    '''
    b64 = hex2b64(hex)
    trialChecksum = 0
    for i in range(len(b64)):
        value = b64toValue(b64[i])
        trialChecksum += value
        trialChecksum %= 256
        print("value:", value, "     total:",  trialChecksum)
    chunkSum = 0
    chunkSum = int(hex, 16)
    chunkSum %= 256
    return trialChecksum


# calculate checksum of chunk
def calcChunkChecksum(hex):
    '''
    calcChunkChecksum takes the data chunk in hexadecimal, and determines how
    much the additional chunk of data would add to the full checksum. It returns
    that value.
    '''
    trialChecksum = 0
    hexstr = str(hex)[1:]  # convert to string, remove leading 'b'
    print(hexstr)
    for i in range(len(hexstr) // 2):
        value = int(hexstr[(2 * i):(2 * i + 2)], 16)
        trialChecksum += value
        trialChecksum %= 256
        print("value:", value, "     total:",  trialChecksum, "     hex[i]:",
            hexstr[2 * i:(2 * i + 2)])
    return trialChecksum


# clean checksum
def cleanChecksum(rawSum):
    '''
    cleanChecksum takes the raw sum and strips the preamble returned by the
    device.
    '''
    (preamble, sum) = rawSum.split("0x")
    return sum


# calculate total checksum
def calcTotalChecksum(prevTotal, hex):
    '''
    calcTotalChecksum determines what the current checksum would be based on
    the previous checksum and the additional new chunk. Since there is an
    element of probability with the device calculating the checksum, two correct
    checksums are possible. The function returns the correct one or, if there is
    an error, returns -1.
    '''
    newTotal = prevTotal + calcChunkChecksum(hex)
    rawChecksum = requestChecksum()
    print("Raw checksum:", rawChecksum)
    appChecksum = int(cleanChecksum(rawChecksum), 16)
    print("Expected checksum:", newTotal, "or", prevTotal)
    print("Checksum returned:", appChecksum)

    # trials
    b64 = hex2b64(hex)
    if b64[-1] == '\n':
        b64 = b64[:-1]
    # if b64[:2] != "0x":
    #     b64 = "0x" + b64

    trialChecksum = 0
    for i in range(len(hex)):
        trialChecksum += int(hex[i], 16)
        trialChecksum %= 256
    # a = base64.b64decode(b64)
    print("Trial checksum:", trialChecksum)

    bTotal = 0
    for char in b64:
        # bTotal += int(base64.b64decode(b64)[1:])
        string = str('b' + (b64toValue(b64)))
        print(string)
        print(bTotal)
        bTotal += int(string)
        bTotal %= 256
        print("bTotal:", bTotal)

    if appChecksum == newTotal:
        return appChecksum
    elif appChecksum == prevTotal:
        return appChecksum
    else:
        return -1


# per chunk
def perChunk(chunk, errors, totalChecksum):
    '''
    Takes a chunk (in hex form) no longer than 20 bytes (20 hex characters) long
    and sends it to device.
    '''
    # convert chunk to base 64
    b64 = hex2b64(hex)

    # send the base64 chunk to the device
    devResponse = sendChunk(b64)

    # evaluate the response from the device
    if devResponse.text == 'ERROR PROCESSING CONTENTS\n':
        errors[1] = True
    elif devResponse.text != 'OK\n':
        errors[2] = True

    # calculate the total checksum, since there is probability involved in
    # creating the checksum on the device.
    totalChecksum = calcTotalChecksum(totalChecksum, hex)

    # evaluate the total checksum to see if an error has been detected
    if totalChecksum == -1:
        errors[0] = True
        # print("checksum error")
    # else:chunk, errors, totalChecksum, hexCCESS")


# run the program
def main():
    # instantiate variables
    totalChecksum = 0
    errors = [False, False, False]

    # open file
    f = open("example.hex")

    # loop through lines of hex
    for hex in f:
        # clean hex
        hex = cleanHex(hex)

        # convert hex to base64
        # b64 = hex2b64(hex)

        # divide into chunks
        chunks = []
        while len(hex) > 20:
            chunks.append(hex[:20])
            hex = hex[20:]

        if len(hex) > 0:
            chunks.append(hex)

        # do per chunk
        for chunk in chunks:
            perChunk(chunk, errors, totalChecksum)

    # return results
    if errors[0]:
        print("A checksum error has occurred. Device should not install",
            "firmware.")
    elif errors[1]:
        print("At least one chunk of data was not correctly processed. Device",
        " should not install firmware.")
    elif errors[2]:
        print("At one point, there was an unexpected response from the device.",
        "The device should not install firmware, and additional investigaton",
        "may be required.")
    else:
        print("Checksum confirms successful transmission. It is safe to install firmware.")

    # close file
    f.close()


if __name__ == '__main__':
    main()
    input('press enter to finish:')
