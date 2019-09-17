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
    hex = rawHex
    if hex[0] == ':':
        hex = hex[1:]
    if hex[-1] == '\n':
        hex = hex[:-1]
    return hex

# convert a line of hex to a line of base64
def hex2b64(hex):
    '''
    This function simplifies transitioning from a line of hex to the base64
    equivalent.
    '''
    a = codecs.decode(hex, 'hex')
    b = codecs.encode(a, 'base64')
    c = b.decode()
    return c[:-1]

# # Convert base 64 to hexadecimal for checksum calculations
def b64toHex(b64):
    '''
    Takes a chunk in b64 and returns that value in decimal form.
    '''
    if b64[-1] == '\n':
        b64 = b64[:-1]
    a = base64.b64decode(b64)
    print(a)
    hex = codecs.encode(a, 'hex')
    return hex

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
def calcChunkChecksum(hex):
    '''
    calcChunkChecksum takes the data chunk in hexadecimal, and determines how much
    the additional chunk of data would add to the full checksum. It returns
    that value.
    '''
    chunkSum = 0
    chunkSum = int(hex, 16)
    chunkSum %= 256
    return chunkSum

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
    appChecksum = int(cleanChecksum(requestChecksum()), 16)
    print("Expected checksum:", newTotal, "or", prevTotal)
    print("Checksum returned:", appChecksum)

    # trials
    b64 = hex2b64(hex)
    if b64[-1] == '\n':
        b64 = b64[:-1]
    # a = base64.b64decode(b64)
    bTotal = 0
    for char in b64:
        # bTotal += int(base64.b64decode(b64)[1:])
        string = str('b'.append(b64toHex(b64)))
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
def perChunk(chunk, errors, totalChecksum, hex):
    '''
    Takes a chunk no longer than 20 bytes (26 base 64 characters) long and sends it to device.
    '''
    # send the base64 chunk to the device
    devResponse = sendChunk(chunk)

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
        b64 = hex2b64(hex)

        # divide into chunks
        chunks = []
        while len(b64) > 26:
            chunks.append(b64[:26])
            b64 = b64[26:]

        if len(b64) > 0:
            chunks.append(b64)

        # do per chunk
        for chunk in chunks:
            perChunk(chunk, errors, totalChecksum, hex)

    # return results
    if errors[0]:
        print("A checksum error has occurred. Device should not install firmware.")
    elif errors[1]:
        print("At least one chunk of data was not correctly processed. Device",
        " should not install firmware.")
    elif errors[2]:
        print("At one point, there was an unexpected response from the device.",
        " The device should not install firmware, and additional investigaton",
        " may be required.")
    else:
        print("Checksum confirms successful transmission. It is safe to install firmware.")


    f.close()


if __name__ == '__main__':
    main()
    input('press enter to finish:')
