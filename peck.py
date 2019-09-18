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
    hexx = str(rawHex)
    if hexx[0] == ':':
        hexx = hexx[1:]
    if hexx[-1] == '\n':
        hexx = hexx[:-1]
    hexx = str.encode(hexx)
    return hexx


# convert a line of hexx to a line of base64
def hex2b64(hexBytes):
    '''
    This function simplifies transitioning from a line of hexx to the base64
    equivalent.
    '''
    # hexBytes = cleanHex(hexBytes)
    # print(hexBytes, "<- hexx, type of hexx ->", type(hexBytes))
    # a = codecs.decode(hexBytes, 'hexx')
    b = codecs.encode(hexBytes, 'base64')
    # print(b, type(b))
    c = b.decode()
    return c[:-1]


# # Convert base 64 to hexadecimal for checksum calculations
def b64toValue(b64):
    '''
    Takes a chunk in b64 and returns that value in decimal form.
    '''
    if b64[-1] == '\n':
        b64 = b64[:-1]
    # b64 = str.encode(b64)
    # hexx = codecs.encode(b64, 'hex')
    return ord(b64)


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
def calcChunkChecksum(hexx, total):
    '''
    calcChunkChecksum takes the data chunk in hexadecimal, and determines how
    much the additional chunk of data would add to the full checksum. It returns
    that value.
    '''
    hexstr = str(hexx)[2:-1]  # convert to string, remove leading 'b' and quotes
    print(hexstr)
    for i in range(len(hexstr)):
        # value = int(hexstr[i], 16)
        value = ord(hexstr[i])
        total += value
        total %= 256
        # print("value:", value, "     total:",  total, "     hexx[i]:",
        #       hexstr[i])
    return total


# clean checksum
def cleanChecksum(rawSum):
    '''
    cleanChecksum takes the raw sum and strips the preamble returned by the
    device. It returns an int
    '''
    (preamble, sum) = rawSum.split("0x")
    sum = int(sum, 16)
    return sum


# calculate total checksum
def calcTotalChecksum(prevTotal, hexx):
    '''
    calcTotalChecksum determines what the current checksum would be based on
    the previous checksum and the additional new chunk. Since there is an
    element of probability with the device calculating the checksum, two correct
    checksums are possible. The function returns the correct one or, if there is
    an error, returns -1.
    '''
    # print(prevTotal)
    # print(hexx)
    prevTotal = int(prevTotal)
    newTotal = calcChunkChecksum(hexx, prevTotal)
    rawChecksum = requestChecksum()
    # print("Raw checksum:", rawChecksum)
    appChecksum = cleanChecksum(rawChecksum)
    print("Expected checksum:", newTotal, "or", prevTotal)
    print("Checksum returned:", appChecksum)

    # trials
    # b64 = hex2b64(hexx)
    # if b64[-1] == '\n':
    #     b64 = b64[:-1]
    # # if b64[:2] != "0x":
    # #     b64 = "0x" + b64
    #
    # trialChecksum = 0
    # for i in range(len(hexx)):
    #     trialChecksum += int(hexx[i], 16)
    #     trialChecksum %= 256
    # # a = base64.b64decode(b64)
    # print("Trial checksum:", trialChecksum)
    #
    # bTotal = 0
    # for char in b64:
    #     # bTotal += int(base64.b64decode(b64)[1:])
    #     string = str('b' + (b64toValue(b64)))
    #     print(string)
    #     print(bTotal)
    #     bTotal += int(string)
    #     bTotal %= 256
    #     print("bTotal:", bTotal)

    if appChecksum == newTotal:
        return appChecksum
    elif appChecksum == prevTotal:
        return appChecksum
    else:
        return -1


# per chunk
def perChunk(chunk, errors, totalChecksum):
    '''
    Takes a chunk (in hex form) no longer than 20 hex characters long
    and sends it to device.
    '''
    # convert chunk to base 64
    b64 = hex2b64(chunk)

    # send the base64 chunk to the device
    devResponse = sendChunk(b64)

    # evaluate the response from the device
    while devResponse.text == 'ERROR PROCESSING CONTENTS\n':
        # print("================ERROR PROCESSING CONTENTS=============")
        # errors[1] = True
        devResponse = sendChunk(b64)
    if devResponse.text != 'OK\n':
        errors[2] = True

    # calculate the total checksum, since there is probability involved in
    # creating the checksum on the device.
    totalChecksum = calcTotalChecksum(totalChecksum, chunk)

    # evaluate the total checksum to see if an error has been detected
    if totalChecksum == -1:
        errors[0] = True
        # print("checksum error")
    # else:chunk, errors, totalChecksum, hexCCESS")

    return totalChecksum


# run the program
def main():
    # instantiate variables
    totalChecksum = cleanChecksum(requestChecksum())
    errors = [False, False, False]

    # open file
    f = open("example.hex")

    # loop through lines of hex
    for hexx in f:
        # clean hexx
        hexx = cleanHex(hexx)

        # convert hex to base64
        # b64 = hex2b64(hex)

        # divide into chunks
        chunks = []
        while len(hexx) > 20:
            chunks.append(hexx[:20])
            hexx = hexx[20:]

        if len(hexx) > 0:
            chunks.append(hexx)

        # do per chunk
        for chunk in chunks:
            totalChecksum = perChunk(chunk, errors, totalChecksum)
            print("official total:", totalChecksum)

    # return results
    if errors[0]:
        print("A checksum error has occurred. Device should not install",
              "firmware.")
    elif errors[1]:
        print("At least one chunk of data was not correctly processed. Device",
              " should not install firmware.")
    elif errors[2]:
        print("At one point, there was an unexpected response from the device.",
              "The device should not install firmware, and additional",
              "investigaton may be required.")
    else:
        print("Checksum confirms successful transmission. It is safe to",
              "install firmware.")

    # close file
    f.close()


if __name__ == '__main__':
    main()
    input('press enter to finish:')
